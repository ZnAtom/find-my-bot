from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class PrivateMessageBatch:
    messages: tuple[str, ...]
    images: tuple[Any, ...]

    @property
    def message(self) -> str:
        return "\n".join(self.messages)


@dataclass
class _PendingBatch:
    version: int = 0
    messages: list[str] = field(default_factory=list)
    images: list[Any] = field(default_factory=list)


class PrivateMessageBatcher:
    # Collect messages until one user has been quiet for the configured window.

    def __init__(self, quiet_seconds: float):
        if quiet_seconds <= 0:
            raise ValueError("quiet_seconds must be positive")
        self.quiet_seconds = quiet_seconds
        self._lock = asyncio.Lock()
        self._pending: dict[str, _PendingBatch] = {}

    async def add_and_wait(
        self,
        key: str,
        *,
        message: str,
        images: list[Any],
    ) -> Optional[PrivateMessageBatch]:
        async with self._lock:
            pending = self._pending.setdefault(key, _PendingBatch())
            pending.version += 1
            version = pending.version
            if message.strip():
                pending.messages.append(message.strip())
            pending.images.extend(images)

        try:
            await asyncio.sleep(self.quiet_seconds)
        except asyncio.CancelledError:
            async with self._lock:
                current = self._pending.get(key)
                if current is not None and current.version == version:
                    self._pending.pop(key, None)
            raise

        async with self._lock:
            current = self._pending.get(key)
            if current is None or current.version != version:
                return None
            self._pending.pop(key, None)
            return PrivateMessageBatch(
                messages=tuple(current.messages),
                images=tuple(current.images),
            )

    async def clear(self) -> None:
        async with self._lock:
            self._pending.clear()
