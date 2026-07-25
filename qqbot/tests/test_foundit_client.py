import asyncio
import sys
import tempfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qqbot.astrbot.plugins.foundit.client import (
    FoundItSupportClient,
    derive_session_key,
    format_image_search_reply,
    format_reply,
)


def test_session_key_is_stable_and_hides_sender_id():
    first = derive_session_key("service-secret", "123456789")
    second = derive_session_key("service-secret", "123456789")

    assert first == second
    assert len(first) == 64
    assert "123456789" not in first


def test_format_reply_absolutizes_and_deduplicates_item_links():
    payload = {
        "answer": "可以查看 /#/lost/12",
        "sources": [
            {"type": "item", "title": "#12 校园卡", "path": "/#/lost/12"},
            {"type": "item", "title": "#12 校园卡", "path": "/#/lost/12"},
        ],
    }

    reply = format_reply(payload, "https://foundit.geekpie.club/")

    assert "https://foundit.geekpie.club/#/lost/12" in reply
    assert reply.count("https://foundit.geekpie.club/#/lost/12") == 1


def test_client_sends_service_auth_and_opaque_session_key():
    async def run_test():
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/integrations/qq/v1/support/chat"
            assert request.headers["authorization"] == "Bearer service-secret"
            body = __import__("json").loads(request.content)
            assert body["session_key"] == "a" * 64
            return httpx.Response(
                200,
                json={
                    "answer": "回答",
                    "sources": [],
                    "intent": "platform_help",
                    "session_id": "f0f62b9b-10b4-4dd8-8db8-f72e5d235e17",
                    "item_results": [],
                },
            )

        client = FoundItSupportClient(
            "https://backend.example",
            "service-secret",
            transport=httpx.MockTransport(handler),
        )
        try:
            payload = await client.chat(message="怎么发布", session_key="a" * 64)
            assert payload["answer"] == "回答"
        finally:
            await client.close()

    asyncio.run(run_test())


def test_format_image_search_reply_contains_analysis_and_safe_link():
    payload = {
        "analysis": {
            "item_name": "蓝色卡片",
            "item_type": "证件卡片",
            "description": "蓝色矩形卡片",
            "notes": [],
        },
        "results": [
            {
                "id": 7,
                "item_name": "蓝色校园卡",
                "direction": "found",
                "location": "一号教学楼",
                "url": "/#/lost/7",
            }
        ],
    }

    reply = format_image_search_reply(payload, "https://foundit.geekpie.club")

    assert "蓝色卡片" in reply
    assert "可能相关的进行中物品" in reply
    assert "https://foundit.geekpie.club/#/lost/7" in reply
    assert "contact" not in reply.lower()


def test_client_uploads_image_as_multipart():
    async def run_test():
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/integrations/qq/v1/support/image-search"
            assert request.headers["authorization"] == "Bearer service-secret"
            assert "multipart/form-data" in request.headers["content-type"]
            assert b"session_key" in request.content
            assert b"image-bytes" in request.content
            return httpx.Response(
                200,
                json={
                    "analysis": {
                        "item_name": "卡片",
                        "item_type": "证件卡片",
                        "description": "测试卡片",
                        "notes": [],
                    },
                    "results": [],
                    "vector_search_used": False,
                },
            )

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image:
            image.write(b"image-bytes")
            image.flush()
            client = FoundItSupportClient(
                "https://backend.example",
                "service-secret",
                transport=httpx.MockTransport(handler),
            )
            try:
                payload = await client.image_search(
                    message="帮我搜索",
                    session_key="a" * 64,
                    image_paths=[image.name],
                )
                assert payload["analysis"]["item_name"] == "卡片"
            finally:
                await client.close()

    asyncio.run(run_test())
