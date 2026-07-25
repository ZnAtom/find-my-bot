import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode, urlparse

import httpx
import jwt
import psycopg2
import psycopg2.extras
from fastapi import HTTPException, Request

from config_env import load_project_env
from db import get_db_connection, release_db_connection

load_project_env()


CASDOOR_ENDPOINT = os.environ.get("CASDOOR_ENDPOINT", "https://auth.geekpie.club").rstrip("/")
CASDOOR_CLIENT_ID = os.environ.get("CASDOOR_CLIENT_ID")
CASDOOR_CLIENT_SECRET = os.environ.get("CASDOOR_CLIENT_SECRET")
CASDOOR_REDIRECT_URI = os.environ.get("CASDOOR_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
CASDOOR_SCOPE = os.environ.get("CASDOOR_SCOPE", "openid profile email")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"
SESSION_COOKIE = os.environ.get("SESSION_COOKIE_NAME", "foundit_session")
STATE_COOKIE = os.environ.get("STATE_COOKIE_NAME", "foundit_oauth_state")
NEXT_COOKIE = os.environ.get("NEXT_COOKIE_NAME", "foundit_oauth_next")
COOKIE_SECURE = os.environ.get("AUTH_COOKIE_SECURE", "0") == "1"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.environ.get("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
OAUTH_STATE_EXPIRE_SECONDS = int(os.environ.get("OAUTH_STATE_EXPIRE_SECONDS", "1800"))
WEAK_JWT_SECRETS = {"dev-change-me", "change-me", "changeme", "secret", "password"}
CSRF_TRUSTED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", FRONTEND_BASE_URL).split(",")
    if origin.strip()
}




def ensure_auth_config():
    missing = [
        name
        for name, value in {
            "CASDOOR_CLIENT_ID": CASDOOR_CLIENT_ID,
            "CASDOOR_CLIENT_SECRET": CASDOOR_CLIENT_SECRET,
            "JWT_SECRET": JWT_SECRET,
        }.items()
        if not value
    ]
    if missing:
        raise HTTPException(status_code=500, detail=f"认证配置缺失: {', '.join(missing)}")
    if JWT_SECRET in WEAK_JWT_SECRETS or len(JWT_SECRET) < 32:
        raise HTTPException(status_code=500, detail="JWT_SECRET 过弱，请使用至少 32 字符的随机密钥")





def make_login_url(state: str) -> str:
    ensure_auth_config()
    query = urlencode(
        {
            "client_id": CASDOOR_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": CASDOOR_REDIRECT_URI,
            "scope": CASDOOR_SCOPE,
            "state": state,
        }
    )
    return f"{CASDOOR_ENDPOINT}/login/oauth/authorize?{query}"


async def exchange_code_for_token(code: str) -> dict:
    ensure_auth_config()
    data = {
        "grant_type": "authorization_code",
        "client_id": CASDOOR_CLIENT_ID,
        "client_secret": CASDOOR_CLIENT_SECRET,
        "code": code,
        "redirect_uri": CASDOOR_REDIRECT_URI,
    }
    transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
    async with httpx.AsyncClient(timeout=20, transport=transport) as client:
        resp = await client.post(f"{CASDOOR_ENDPOINT}/api/login/oauth/access_token", data=data)
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Casdoor token 交换失败")
    payload = resp.json()
    if "access_token" not in payload:
        raise HTTPException(status_code=401, detail="Casdoor token 响应缺少 access_token")
    return payload


async def get_casdoor_userinfo(access_token: str) -> dict:
    transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
    async with httpx.AsyncClient(timeout=20, transport=transport) as client:
        resp = await client.get(
            f"{CASDOOR_ENDPOINT}/api/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Casdoor 用户信息获取失败")
    return resp.json()


def _pick_first(*values) -> Optional[str]:
    for value in values:
        if value:
            return str(value)
    return None


def _student_id_from_userinfo(userinfo: dict) -> str:
    properties = userinfo.get("properties") or {}
    return _pick_first(
        userinfo.get("student_id"),
        properties.get("student_id"),
        userinfo.get("preferred_username"),
        userinfo.get("name"),
        userinfo.get("id"),
        userinfo.get("sub"),
    ) or "unknown"


def _display_name_from_userinfo(userinfo: dict) -> str:
    return _pick_first(
        userinfo.get("displayName"),
        userinfo.get("display_name"),
        userinfo.get("name"),
        userinfo.get("preferred_username"),
        userinfo.get("sub"),
    ) or "Casdoor 用户"


def _serialize_user(row) -> dict:
    user = dict(row)
    for key, value in list(user.items()):
        if isinstance(value, datetime):
            user[key] = value.isoformat()
    user.pop("casdoor_sub", None)
    return user


def get_or_create_user(userinfo: dict):
    """返回 (user_dict, is_new) 元组 — is_new 为 True 表示首次创建用户"""
    casdoor_sub = _pick_first(userinfo.get("sub"), userinfo.get("id"), userinfo.get("name"))
    if not casdoor_sub:
        raise HTTPException(status_code=401, detail="Casdoor 用户信息缺少唯一标识")

    student_id = _student_id_from_userinfo(userinfo)
    name = _display_name_from_userinfo(userinfo)
    email = userinfo.get("email")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE casdoor_sub = %s", (casdoor_sub,))
        row = cur.fetchone()
        if row:
            # 已存在用户：更新 Casdoor 原始名，并获取/更新邮箱
            new_email = email if email else row["email"]
            cur.execute(
                """UPDATE users
                   SET casdoor_name = %s, email = %s
                   WHERE id = %s
                   RETURNING *""",
                (userinfo.get("name"), new_email, row["id"]),
            )
            updated_row = cur.fetchone()
            conn.commit()
            return _serialize_user(updated_row), False

        cur.execute("SELECT * FROM users WHERE student_id = %s", (student_id,))
        row = cur.fetchone()
        if row:
            # 链接 Casdoor 账号到已有本地用户，并获取/更新邮箱
            new_email = email if email else row["email"]
            cur.execute(
                """UPDATE users
                   SET casdoor_sub = %s,
                       casdoor_name = %s,
                       email = %s
                   WHERE id = %s
                   RETURNING *""",
                (casdoor_sub, userinfo.get("name"), new_email, row["id"]),
            )
            updated_row = cur.fetchone()
            conn.commit()
            return _serialize_user(updated_row), False

        cur.execute(
            """INSERT INTO users (student_id, name, email, casdoor_sub, casdoor_name, role)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING *""",
            (student_id, name, email, casdoor_sub, userinfo.get("name"), "user"),
        )
        new_row = cur.fetchone()
        conn.commit()
        return _serialize_user(new_row), True
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=409, detail="本地用户创建失败：学号或 Casdoor 账号已存在")
    finally:
        cur.close()
        release_db_connection(conn)


def create_session_token(user_id: int) -> str:
    ensure_auth_config()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> int:
    ensure_auth_config()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="登录状态无效或已过期")


def get_current_user(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="请先登录")

    user_id = decode_session_token(token)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        return _serialize_user(user)
    finally:
        cur.close()
        release_db_connection(conn)


def get_optional_user(request: Request) -> Optional[dict]:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        return get_current_user(request)
    except HTTPException:
        return None


def require_admin(request: Request) -> dict:
    user = get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def assert_owner_or_admin(item_id: int, user: dict):
    if user.get("role") == "admin":
        return

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT user_id FROM lost_items WHERE id = %s", (item_id,))
        item = cur.fetchone()
        if not item:
            raise HTTPException(status_code=404, detail="物品不存在")
        if item["user_id"] is None or item["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="只能操作自己发布的物品")
    finally:
        cur.close()
        release_db_connection(conn)


def new_state() -> str:
    return secrets.token_urlsafe(32)


def safe_frontend_redirect(path: Optional[str]) -> str:
    if not path or not path.startswith("/"):
        return f"{FRONTEND_BASE_URL}/"
    if path.startswith("//"):
        return f"{FRONTEND_BASE_URL}/"
    return f"{FRONTEND_BASE_URL}{path}"


def _origin_from_header(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def verify_csrf_origin(request: Request):
    origin = _origin_from_header(request.headers.get("origin"))
    referer = _origin_from_header(request.headers.get("referer"))
    request_origin = origin or referer

    if not request_origin and request.headers.get("sec-fetch-site") == "same-origin":
        return

    if not request_origin or request_origin.rstrip("/") not in CSRF_TRUSTED_ORIGINS:
        raise HTTPException(status_code=403, detail="请求来源校验失败")
