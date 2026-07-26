from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, _extract_school_response_text, _normalize_uploaded_image_urls, _rate_limit_buckets, serialize_item_for_user
from auth import normalize_school_email, require_casdoor_email_verified, require_verified_school_email
from embedding import embedding_enabled, encode_text

client = TestClient(app)
IMAGE_ANALYSIS_TEST_IMAGE_URL = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg"
AUTH_USER = {
    "id": 1,
    "student_id": "test",
    "name": "测试用户",
    "role": "user",
    "school_email": "test@shanghaitech.edu.cn",
    "school_email_verified_at": "2026-07-26T10:00:00",
}
ADMIN_USER = {"id": 2, "student_id": "admin", "name": "管理员", "role": "admin"}


def sensitive_item(contact_visibility="private"):
    return {
        "id": 10,
        "item_name": "校园卡",
        "item_type": "证件卡片",
        "direction": "found",
        "status": "active",
        "description": "印有姓名和学号的校园卡",
        "image_url": "/uploads/card.jpg",
        "location": "上海科技大学 · 生活区 · 学生宿舍8号楼 · 一楼",
        "contact_visibility": contact_visibility,
        "contact_person": "王同学",
        "contact_phone": "13800000000",
        "contact_qq": "123456",
        "contact_email": "test@example.com",
        "storage_location": "图书馆前台",
        "user_id": AUTH_USER["id"],
    }

def test_read_main():
    response = client.get("/docs")
    assert response.status_code == 200


def test_embedding_can_be_disabled(monkeypatch):
    monkeypatch.setenv("EMBEDDING_ENABLED", "0")

    assert embedding_enabled() is False
    with pytest.raises(RuntimeError, match="disabled"):
        encode_text("校园卡")


def test_extract_school_response_text_supports_openai_choices():
    data = {"choices": [{"message": {"content": '{"item_name":"黑色水杯"}'}}]}

    assert _extract_school_response_text(data) == '{"item_name":"黑色水杯"}'


def test_extract_school_response_text_supports_wrapped_output():
    data = {"code": 0, "data": {"output": {"text": '{"item_name":"蓝色雨伞"}'}}}

    assert _extract_school_response_text(data) == '{"item_name":"蓝色雨伞"}'

@patch("app.release_db_connection")
@patch("app.get_db_connection")
def test_api_lost_items_no_auth(mock_db, mock_release_db):
    response = client.get("/api/lost-items")
    assert response.status_code in [200, 401]

@patch("app.get_db_connection")
def test_upload_without_trusted_origin_is_forbidden(mock_db):
    response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", b"dummy content", "image/jpeg")}
    )
    assert response.status_code == 403

@patch("app.get_db_connection")
def test_upload_allows_anonymous_with_trusted_origin(mock_db):
    response = client.post(
        "/api/upload",
        headers={"Origin": "http://localhost:5173"},
        files={"file": ("test.jpg", b"dummy content", "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.json()["url"].startswith("/uploads/")


@patch("app.UPLOAD_RATE_LIMIT_COUNT", 1)
@patch("app.UPLOAD_RATE_LIMIT_WINDOW_SECONDS", 60)
@patch("app.get_db_connection")
def test_upload_rate_limit_returns_429(mock_db):
    _rate_limit_buckets.clear()
    headers = {"Origin": "http://localhost:5173", "X-Forwarded-For": "198.51.100.10"}

    first_response = client.post(
        "/api/upload",
        headers=headers,
        files={"file": ("first.jpg", b"dummy content", "image/jpeg")}
    )
    second_response = client.post(
        "/api/upload",
        headers=headers,
        files={"file": ("second.jpg", b"dummy content", "image/jpeg")}
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    _rate_limit_buckets.clear()


def test_normalize_uploaded_image_urls_blocks_external_url():
    with pytest.raises(HTTPException) as exc:
        _normalize_uploaded_image_urls("https://example.com/uploads/test.jpg")
    assert exc.value.status_code == 400


def test_normalize_uploaded_image_urls_requires_uploaded_file(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    (upload_dir / "safe.jpg").write_bytes(b"image")
    monkeypatch.setattr("app.UPLOAD_DIR", str(upload_dir))

    assert _normalize_uploaded_image_urls("/uploads/safe.jpg") == "/uploads/safe.jpg"

    with pytest.raises(HTTPException) as exc:
        _normalize_uploaded_image_urls("/uploads/missing.jpg")
    assert exc.value.status_code == 400


def test_sensitive_uploaded_image_requires_verified_school_user(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    (upload_dir / "card.jpg").write_bytes(b"image")
    monkeypatch.setattr("app.UPLOAD_DIR", str(upload_dir))

    cursor = type("Cursor", (), {
        "execute": lambda self, *_args, **_kwargs: None,
        "fetchall": lambda self: [{
            "id": 10,
            "item_type": "证件卡片",
            "user_id": AUTH_USER["id"],
            "image_url": "/uploads/card.jpg",
        }],
        "close": lambda self: None,
    })()
    conn = type("Connection", (), {"cursor": lambda self, **_kwargs: cursor})()

    with patch("app.get_db_connection", return_value=conn), \
         patch("app.release_db_connection"), \
         patch("app.get_optional_user", return_value=None):
        anonymous_response = client.get("/uploads/card.jpg")

    assert anonymous_response.status_code == 403

    with patch("app.get_db_connection", return_value=conn), \
         patch("app.release_db_connection"), \
         patch("app.get_optional_user", return_value=AUTH_USER):
        verified_response = client.get("/uploads/card.jpg")

    assert verified_response.status_code == 200
    assert verified_response.headers["cache-control"] == "private, no-store"


def test_private_contact_fields_are_masked_for_anonymous_user():
    item = serialize_item_for_user(sensitive_item(), None)

    assert item["contact_person"] == "匿名"
    assert item["contact_phone"] is None
    assert item["contact_qq"] is None
    assert item["contact_email"] is None
    assert item["storage_location"] is None
    assert item["item_name"] == "证件卡片"
    assert item["description"] is None
    assert item["image_url"] is None
    assert item["location"] == "生活区 · 学生宿舍8号楼"
    assert item["sensitive_content_hidden"] is True
    assert item["contact_access_granted"] is False
    assert item["storage_access_granted"] is False


def test_private_contact_fields_are_visible_to_owner_and_admin():
    owner_item = serialize_item_for_user(sensitive_item(), AUTH_USER)
    admin_item = serialize_item_for_user(sensitive_item(), ADMIN_USER)

    assert owner_item["contact_phone"] == "13800000000"
    assert owner_item["storage_location"] == "图书馆前台"
    assert admin_item["contact_email"] == "test@example.com"
    assert admin_item["storage_location"] == "图书馆前台"


def test_logged_in_contact_fields_require_verified_school_email_and_do_not_reveal_storage():
    viewer = {
        "id": 3,
        "role": "user",
        "school_email": "viewer@shanghaitech.edu.cn",
        "school_email_verified_at": "2026-07-26T10:00:00",
    }
    item = serialize_item_for_user(sensitive_item("logged_in"), viewer)

    assert item["contact_person"] == "王同学"
    assert item["contact_phone"] == "13800000000"
    assert item["description"] == "印有姓名和学号的校园卡"
    assert item["image_url"] == "/uploads/card.jpg"
    assert item["storage_location"] is None
    assert item["storage_access_granted"] is False


def test_public_contact_fields_are_visible_to_anonymous_user():
    source = sensitive_item("public")
    source["item_type"] = "其他"
    item = serialize_item_for_user(source, None)

    assert item["contact_person"] == "王同学"
    assert item["contact_phone"] == "13800000000"
    assert item["contact_qq"] == "123456"
    assert item["contact_email"] == "test@example.com"
    assert item["storage_location"] is None


def test_claimed_contact_fields_are_visible_to_related_claim_user():
    viewer = {
        "id": 3,
        "role": "user",
        "school_email": "viewer@shanghaitech.edu.cn",
        "school_email_verified_at": "2026-07-26T10:00:00",
    }
    item = serialize_item_for_user(sensitive_item("claimed"), viewer, {10})

    assert item["contact_qq"] == "123456"
    assert item["contact_email"] == "test@example.com"
    assert item["storage_location"] == "图书馆前台"
    assert item["storage_access_granted"] is True


def test_school_email_validation_accepts_root_and_subdomains():
    assert normalize_school_email(" Student@ShanghaiTech.edu.cn ") == "student@shanghaitech.edu.cn"
    assert normalize_school_email("student@mail.shanghaitech.edu.cn") == "student@mail.shanghaitech.edu.cn"


def test_casdoor_explicitly_unverified_email_is_rejected():
    with pytest.raises(HTTPException) as exc:
        require_casdoor_email_verified({"email_verified": False})
    assert exc.value.status_code == 403

    require_casdoor_email_verified({"email_verified": True})
    require_casdoor_email_verified({})


@pytest.mark.parametrize("email", [
    "student@example.com",
    "student@shanghaitech.edu.cn.example.com",
    "student@fakeshanghaitech.edu.cn",
    "not-an-email",
])
def test_school_email_validation_rejects_non_school_domains(email):
    with pytest.raises(HTTPException) as exc:
        normalize_school_email(email)
    assert exc.value.status_code == 403
    assert "上海科技大学邮箱" in exc.value.detail


def test_verified_school_email_is_required_for_claims():
    with pytest.raises(HTTPException) as exc:
        require_verified_school_email({"id": 3, "school_email": "student@shanghaitech.edu.cn"})
    assert exc.value.status_code == 403


class ClaimTestCursor:
    def __init__(self):
        self.statements = []
        self.next_row = None

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        if "FROM lost_items" in sql and "FOR UPDATE" in sql:
            self.next_row = {
                "id": 10,
                "item_name": "校园卡",
                "direction": "found",
                "status": "active",
                "user_id": None,
                "contact_person": "匿名",
                "storage_location": "二号门保安室",
            }
        elif "SELECT COUNT(*)" in sql:
            self.next_row = (0,)
        elif "INSERT INTO claim_requests" in sql:
            self.next_row = {
                "id": 20,
                "item_id": 10,
                "requester_user_id": AUTH_USER["id"],
                "owner_user_id": None,
                "request_type": "claim",
                "requester_name": "测试用户",
                "requester_contact": AUTH_USER["school_email"],
                "requester_school_email": AUTH_USER["school_email"],
                "message": None,
                "status": "completed",
                "created_at": "2026-07-26T10:00:00",
            }

    def fetchone(self):
        return self.next_row

    def close(self):
        pass


class ClaimTestConnection:
    def __init__(self):
        self.test_cursor = ClaimTestCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self, **_kwargs):
        return self.test_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


@patch("app.release_db_connection")
@patch("app.get_current_user", return_value=AUTH_USER)
def test_claim_records_school_email_snapshot_before_returning_storage(mock_user, mock_release):
    conn = ClaimTestConnection()
    with patch("app.get_db_connection", return_value=conn):
        response = client.post(
            "/api/lost-items/10/claim",
            headers={"Origin": "http://localhost:5173"},
            json={
                "requester_name": "测试用户",
                "requester_contact": AUTH_USER["school_email"],
            },
        )

    assert response.status_code == 200
    assert response.json()["requester_school_email"] == AUTH_USER["school_email"]
    assert response.json()["storage_location"] == "二号门保安室"
    assert conn.committed is True
    insert = next(entry for entry in conn.test_cursor.statements if "INSERT INTO claim_requests" in entry[0])
    assert "requester_school_email" in insert[0]
    assert AUTH_USER["school_email"] in insert[1]


def test_campus_map_tile_rejects_out_of_range_zoom():
    response = client.get("/api/campus-map/tiles/16/tile1_1.png")
    assert response.status_code == 404


@patch("app.get_db_connection")
def test_image_analysis_without_trusted_origin_is_forbidden(mock_db):
    response = client.post(
        "/api/image-analysis",
        json={"image_urls": [IMAGE_ANALYSIS_TEST_IMAGE_URL]}
    )
    assert response.status_code == 403


@patch("app._call_school_image_analysis")
@patch("app.get_db_connection")
def test_image_analysis_allows_trusted_origin_without_auth(mock_db, mock_analysis):
    mock_analysis.return_value = {
        "item_name": "测试物品",
        "item_type": "其他",
        "description": "固定测试结果",
        "notes": [],
    }

    response = client.post(
        "/api/image-analysis",
        headers={"Origin": "http://localhost:5173"},
        json={"image_urls": [IMAGE_ANALYSIS_TEST_IMAGE_URL]}
    )

    assert response.status_code == 200
    assert response.json()["item_name"] == "测试物品"
    mock_analysis.assert_awaited_once_with([IMAGE_ANALYSIS_TEST_IMAGE_URL])


def test_logout_without_trusted_origin_is_forbidden():
    response = client.post("/api/auth/logout")
    assert response.status_code == 403


@patch("app.get_current_user", return_value=AUTH_USER)
def test_update_profile_without_trusted_origin_is_forbidden(mock_user):
    response = client.put("/api/me", json={"name": "新名字"})
    assert response.status_code == 403


@patch("app.get_current_user", return_value=AUTH_USER)
def test_mark_notification_read_without_trusted_origin_is_forbidden(mock_user):
    response = client.put("/api/notifications/1/read")
    assert response.status_code == 403


@patch("app.get_current_user", return_value=AUTH_USER)
def test_create_claim_without_trusted_origin_is_forbidden(mock_user):
    response = client.post(
        "/api/lost-items/1/claim",
        json={"requester_name": "张同学", "requester_contact": "test@example.com"}
    )
    assert response.status_code == 403


@patch("app.require_admin", return_value=ADMIN_USER)
def test_create_user_without_trusted_origin_is_forbidden(mock_admin):
    response = client.post(
        "/api/users",
        json={"student_id": "20260001", "name": "测试用户"}
    )
    assert response.status_code == 403


@patch("app.require_admin", return_value=ADMIN_USER)
def test_update_user_without_trusted_origin_is_forbidden(mock_admin):
    response = client.put("/api/users/1", json={"role": "admin"})
    assert response.status_code == 403


def test_create_lost_item_without_trusted_origin_is_forbidden():
    response = client.post(
        "/api/lost-items",
        json={"item_name": "测试物品", "direction": "found"}
    )
    assert response.status_code == 403


@patch("app.get_current_user", return_value=AUTH_USER)
def test_update_lost_item_without_trusted_origin_is_forbidden(mock_user):
    response = client.put("/api/lost-items/1", json={"item_name": "新名称"})
    assert response.status_code == 403


@patch("app.get_current_user", return_value=AUTH_USER)
def test_delete_lost_item_without_trusted_origin_is_forbidden(mock_user):
    response = client.delete("/api/lost-items/1")
    assert response.status_code == 403
