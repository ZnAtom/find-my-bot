from __future__ import annotations

import os

import httpx

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
import astrbot.api.message_components as Comp
from astrbot.api.star import Context, Star

from .batching import PrivateMessageBatcher
from .client import (
    FoundItSupportClient,
    SupportClientError,
    derive_session_key,
    format_image_search_reply,
    format_reply,
)


class FoundItPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.service_token = str(config.get("service_token", "")).strip()
        self.site_base_url = str(config.get("site_base_url", "https://foundit.geekpie.club")).strip()
        self.client = FoundItSupportClient(
            str(config.get("backend_base_url", "http://host.docker.internal:8000")),
            self.service_token,
            timeout_seconds=float(config.get("timeout_seconds", 90)),
        )
        self._session_ids: dict[str, str] = {}
        quiet_seconds = min(15.0, max(1.0, float(config.get("batch_window_seconds", 5))))
        self._private_batcher = PrivateMessageBatcher(quiet_seconds)

    @filter.command("foundit_ping")
    async def ping(self, event: AstrMessageEvent):
        """检查 FoundIt QQ 插件是否已经加载。"""
        event.stop_event()
        yield event.plain_result("FoundIt QQ 通道正常")

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def private_support(self, event: AstrMessageEvent):
        """把 QQ 私聊消息聚合后转发给 FoundIt 网站智能客服。"""
        message = (event.message_str or "").strip()
        images = [
            component
            for component in event.get_messages()
            if isinstance(component, Comp.Image)
        ]
        if (not message and not images) or message.startswith("/foundit_ping"):
            return

        event.stop_event()
        if not self.service_token:
            yield event.plain_result("FoundIt QQ 客服尚未配置，请联系管理员。")
            return

        session_key = derive_session_key(self.service_token, str(event.get_sender_id()))
        batch = await self._private_batcher.add_and_wait(
            session_key,
            message=message,
            images=images,
        )
        if batch is None:
            return

        message = batch.message
        images = list(batch.images)
        if len(images) > 3:
            yield event.plain_result("单次最多处理 3 张图片，请减少图片后重试。")
            return

        try:
            if images:
                image_paths = []
                for image in images:
                    try:
                        path = await image.convert_to_file_path()
                    except Exception as exc:
                        raise SupportClientError("QQ 图片下载失败，请重新发送") from exc
                    if not os.path.isfile(path):
                        raise SupportClientError("QQ 图片下载失败，请重新发送")
                    if os.path.getsize(path) > 5 * 1024 * 1024:
                        raise SupportClientError("单张图片不能超过 5MB")
                    image_paths.append(path)
                payload = await self.client.image_search(
                    message=message,
                    session_key=session_key,
                    image_paths=image_paths,
                )
                yield event.plain_result(
                    format_image_search_reply(payload, self.site_base_url)
                )
                return

            payload = await self.client.chat(
                message=message,
                session_key=session_key,
                session_id=self._session_ids.get(session_key),
            )
            session_id = payload.get("session_id")
            if isinstance(session_id, str) and session_id:
                self._session_ids[session_key] = session_id
            yield event.plain_result(format_reply(payload, self.site_base_url))
        except SupportClientError as exc:
            logger.warning("FoundIt support request rejected: %s", exc)
            yield event.plain_result(str(exc))
        except (httpx.HTTPError, ValueError):
            logger.exception("FoundIt support request failed")
            yield event.plain_result("FoundIt 智能客服暂时不可用，请稍后再试。")

    async def terminate(self):
        await self._private_batcher.clear()
        await self.client.close()
