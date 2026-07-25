import io
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
from fastapi.testclient import TestClient

from app import QQSupportChatRequest, _service_bearer_is_valid


client = TestClient(app_module.app)
SESSION_KEY = "a" * 64


def test_service_bearer_requires_exact_nonempty_token():
    assert _service_bearer_is_valid("Bearer expected-token", "expected-token")
    assert not _service_bearer_is_valid("Bearer wrong-token", "expected-token")
    assert not _service_bearer_is_valid("expected-token", "expected-token")
    assert not _service_bearer_is_valid("Bearer anything", "")


def test_qq_support_request_accepts_opaque_session_key():
    payload = QQSupportChatRequest(message="怎么发布招领", session_key=SESSION_KEY)

    assert payload.message == "怎么发布招领"
    assert payload.session_id is None


def test_qq_route_rejects_missing_service_auth_before_database(monkeypatch):
    monkeypatch.setattr(app_module, "QQ_BOT_SERVICE_TOKEN", "expected-token")

    def fail_if_called():
        raise AssertionError("database must not be touched before service authentication")

    monkeypatch.setattr(app_module, "get_db_connection", fail_if_called)
    response = client.post(
        "/api/integrations/qq/v1/support/chat",
        json={"message": "怎么发布", "session_key": SESSION_KEY},
    )

    assert response.status_code == 401


def test_qq_route_calls_shared_support_core_with_hashed_identity(monkeypatch):
    captured = {}
    connection = object()
    monkeypatch.setattr(app_module, "QQ_BOT_SERVICE_TOKEN", "expected-token")
    monkeypatch.setattr(app_module, "get_db_connection", lambda: connection)
    monkeypatch.setattr(app_module, "release_db_connection", lambda conn: None)
    app_module._rate_limit_buckets.clear()

    async def fake_answer(conn, **kwargs):
        captured["conn"] = conn
        captured.update(kwargs)
        return {
            "answer": "回答",
            "sources": [],
            "intent": "platform_help",
            "session_id": "f0f62b9b-10b4-4dd8-8db8-f72e5d235e17",
            "item_results": [],
        }

    monkeypatch.setattr(app_module, "answer_support_chat", fake_answer)
    response = client.post(
        "/api/integrations/qq/v1/support/chat",
        headers={"Authorization": "Bearer expected-token"},
        json={"message": "怎么发布", "session_key": SESSION_KEY},
    )

    assert response.status_code == 200
    assert captured["conn"] is connection
    assert captured["channel"] == "qq"
    assert captured["user"] is None
    assert captured["anonymous_key"] != SESSION_KEY
    assert len(captured["anonymous_key"]) == 40


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 24), (20, 80, 160)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_qq_image_search_rejects_invalid_image(monkeypatch):
    monkeypatch.setattr(app_module, "QQ_BOT_SERVICE_TOKEN", "expected-token")
    app_module._rate_limit_buckets.clear()

    response = client.post(
        "/api/integrations/qq/v1/support/image-search",
        headers={"Authorization": "Bearer expected-token"},
        data={"message": "帮我找找", "session_key": SESSION_KEY},
        files={"files": ("fake.jpg", b"not-an-image", "image/jpeg")},
    )

    assert response.status_code == 400
    assert "有效图片" in response.json()["detail"]


def test_qq_image_search_uses_temp_file_and_returns_safe_results(monkeypatch):
    observed_paths = []
    connection = object()
    monkeypatch.setattr(app_module, "QQ_BOT_SERVICE_TOKEN", "expected-token")
    monkeypatch.setattr(app_module, "get_db_connection", lambda: connection)
    monkeypatch.setattr(app_module, "release_db_connection", lambda conn: None)
    monkeypatch.setattr(app_module, "_qq_image_query_embedding", lambda *args: None)
    app_module._rate_limit_buckets.clear()

    async def fake_analysis(paths):
        observed_paths.extend(paths)
        assert all(os.path.isfile(path) for path in paths)
        return app_module.ImageAnalysisResponse(
            item_name="蓝色卡片",
            item_type="证件卡片",
            description="蓝色矩形卡片",
            notes=[],
        )

    def fake_search(conn, query, limit, *, query_embedding=None):
        assert conn is connection
        assert query == "蓝色卡片"
        assert query_embedding is None
        return [
            {
                "id": 7,
                "item_name": "蓝色校园卡",
                "item_type": "证件卡片",
                "direction": "found",
                "status": "active",
                "description": "蓝色卡片",
                "location": "一号教学楼",
                "url": "/#/lost/7",
            }
        ]

    monkeypatch.setattr(app_module, "_call_school_image_analysis", fake_analysis)
    monkeypatch.setattr(app_module, "search_public_items", fake_search)

    response = client.post(
        "/api/integrations/qq/v1/support/image-search",
        headers={"Authorization": "Bearer expected-token"},
        data={"message": "这张卡有人捡到吗", "session_key": SESSION_KEY},
        files={"files": ("card.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis"]["item_name"] == "蓝色卡片"
    assert body["results"][0]["id"] == 7
    assert "contact_phone" not in str(body)
    assert observed_paths
    assert all(not os.path.exists(path) for path in observed_paths)
