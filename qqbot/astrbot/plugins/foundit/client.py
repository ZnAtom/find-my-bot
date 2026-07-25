from __future__ import annotations

import hashlib
import hmac
import mimetypes
import os
import re
from typing import Any, Optional

import httpx


class SupportClientError(RuntimeError):
    pass


def derive_session_key(service_token: str, sender_id: str) -> str:
    """Derive a stable opaque key without sending or storing the raw QQ number."""
    return hmac.new(
        service_token.encode("utf-8"),
        f"qq-private:{sender_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def format_image_search_reply(
    payload: dict[str, Any],
    site_base_url: str,
    max_chars: int = 3500,
) -> str:
    analysis = payload.get("analysis") if isinstance(payload.get("analysis"), dict) else {}
    item_name = str(analysis.get("item_name") or "未能确定物品名称").strip()
    item_type = str(analysis.get("item_type") or "未分类").strip()
    description = str(analysis.get("description") or "暂无明确外观描述").strip()

    lines = [
        "图片识别结果（请核对）：",
        f"物品：{item_name}",
        f"分类：{item_type}",
        f"描述：{description}",
    ]
    notes = analysis.get("notes")
    if isinstance(notes, list) and notes:
        lines.append("提示：" + "；".join(str(note) for note in notes[:3] if str(note).strip()))

    results = payload.get("results")
    if isinstance(results, list) and results:
        lines.append("")
        lines.append("可能相关的进行中物品：")
        base_url = site_base_url.rstrip("/")
        for index, item in enumerate(results[:5], start=1):
            if not isinstance(item, dict):
                continue
            direction = "招领" if item.get("direction") == "found" else "寻物"
            location = str(item.get("location") or "地点未填写").strip()
            path = str(item.get("url") or "").strip()
            if path.startswith("/#") and base_url:
                path = f"{base_url}{path}"
            lines.append(
                f"{index}. #{item.get('id')} {item.get('item_name') or '未命名物品'}"
                f"（{direction}，{location}）"
            )
            if path:
                lines.append(path)
        lines.append("以上仅为相似线索，请进入详情页核验。")
    else:
        lines.extend(["", "暂未找到相关的进行中物品。"])

    reply = "\n".join(lines)
    if len(reply) > max_chars:
        reply = reply[: max_chars - 12].rstrip() + "\n（回复过长）"
    return reply


def format_reply(payload: dict[str, Any], site_base_url: str, max_chars: int = 3500) -> str:
    base_url = site_base_url.rstrip("/")
    answer = str(payload.get("answer") or "暂时没有可用回答。").strip()
    if base_url:
        answer = re.sub(r"(?<!\w)/#/lost/(\d+)", rf"{base_url}/#/lost/\1", answer)

    links: list[str] = []
    seen: set[str] = set()
    for source in payload.get("sources") or []:
        if not isinstance(source, dict) or source.get("type") != "item":
            continue
        path = str(source.get("path") or "").strip()
        if path.startswith("/#") and base_url:
            path = f"{base_url}{path}"
        if not path or path in seen:
            continue
        seen.add(path)
        title = str(source.get("title") or "物品详情").strip()
        links.append(f"{title}: {path}")

    if links and not all(link.split(": ", 1)[-1] in answer for link in links):
        answer = f"{answer}\n\n相关物品：\n" + "\n".join(links)

    if len(answer) > max_chars:
        answer = answer[: max_chars - 12].rstrip() + "\n（回复过长）"
    return answer


class FoundItSupportClient:
    def __init__(
        self,
        backend_base_url: str,
        service_token: str,
        *,
        timeout_seconds: float = 90,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.backend_base_url = backend_base_url.rstrip("/")
        self.service_token = service_token.strip()
        self.timeout_seconds = timeout_seconds
        self._client = httpx.AsyncClient(
            timeout=timeout_seconds,
            transport=transport,
            follow_redirects=False,
        )

    async def chat(
        self,
        *,
        message: str,
        session_key: str,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        if not self.backend_base_url or not self.service_token:
            raise SupportClientError("FoundIt QQ 客服尚未配置")

        response = await self._client.post(
            f"{self.backend_base_url}/api/integrations/qq/v1/support/chat",
            headers={"Authorization": f"Bearer {self.service_token}"},
            json={
                "message": message,
                "session_key": session_key,
                "session_id": session_id,
            },
        )
        if response.status_code >= 400:
            detail = ""
            try:
                body = response.json()
                if isinstance(body, dict) and isinstance(body.get("detail"), str):
                    detail = body["detail"]
            except ValueError:
                pass
            if response.status_code == 429:
                raise SupportClientError("消息发送太频繁，请稍后再试")
            if response.status_code in {401, 403, 503}:
                raise SupportClientError("FoundIt QQ 客服配置错误，请联系管理员")
            raise SupportClientError(detail or "FoundIt 智能客服暂时不可用")

        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("answer"), str):
            raise SupportClientError("FoundIt 智能客服返回格式异常")
        return payload

    async def image_search(
        self,
        *,
        message: str,
        session_key: str,
        image_paths: list[str],
    ) -> dict[str, Any]:
        if not self.backend_base_url or not self.service_token:
            raise SupportClientError("FoundIt QQ 客服尚未配置")
        if not image_paths:
            raise SupportClientError("没有可处理的 QQ 图片")

        handles = []
        multipart_files = []
        try:
            for path in image_paths:
                handle = open(path, "rb")
                handles.append(handle)
                content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
                multipart_files.append(
                    ("files", (os.path.basename(path), handle, content_type))
                )

            response = await self._client.post(
                f"{self.backend_base_url}/api/integrations/qq/v1/support/image-search",
                headers={"Authorization": f"Bearer {self.service_token}"},
                data={"message": message, "session_key": session_key},
                files=multipart_files,
                timeout=max(self.timeout_seconds, 240),
            )
        finally:
            for handle in handles:
                handle.close()

        if response.status_code >= 400:
            detail = ""
            try:
                body = response.json()
                if isinstance(body, dict) and isinstance(body.get("detail"), str):
                    detail = body["detail"]
            except ValueError:
                pass
            if response.status_code == 429:
                raise SupportClientError("图片识别请求太频繁，请稍后再试")
            if response.status_code in {401, 403, 503}:
                raise SupportClientError("FoundIt QQ 客服配置错误，请联系管理员")
            raise SupportClientError(detail or "QQ 图片识别与搜索暂时不可用")

        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("analysis"), dict):
            raise SupportClientError("QQ 图片识别返回格式异常")
        return payload

    async def close(self) -> None:
        await self._client.aclose()
