from fastapi import FastAPI, HTTPException, Query, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
import psycopg2.extras
import os
import uuid
import aiofiles
from functools import lru_cache
from urllib.parse import unquote, urlparse
from auth import (
    COOKIE_SECURE,
    NEXT_COOKIE,
    OAUTH_STATE_EXPIRE_SECONDS,
    SESSION_COOKIE,
    STATE_COOKIE,
    assert_owner_or_admin,
    create_session_token,
    exchange_code_for_token,
    get_casdoor_userinfo,
    get_current_user,
    get_or_create_user,
    get_optional_user,
    make_login_url,
    new_state,
    require_admin,
    safe_frontend_redirect,
    verify_csrf_origin,
)
from embedding import encode_text, encode_multimodal, init_model
from db import get_db_connection, release_db_connection
from email_sender import send_match_email

app = FastAPI(title="校园失物招领 API", version="1.0.0")


import asyncio
import logging

CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]

@app.on_event("startup")
def startup():
    init_model()
    asyncio.create_task(periodic_email_matcher())

async def periodic_email_matcher():
    while True:
        try:
            # Sleep first or wait for the specific time. Let's sleep for 24h.
            # In a real system, this would be cron-like, e.g. apscheduler.
            await asyncio.sleep(86400)
            logging.info("Running daily email matcher for active lost/found items...")
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Active lost/found entries are matched against the opposite direction.
            cur.execute("""
                SELECT l.id, l.item_name, l.direction, l.contact_person, u.email, l.vector
                FROM lost_items l
                LEFT JOIN users u ON l.user_id = u.id
                WHERE l.status = 'active'
                  AND l.direction IN ('lost', 'found')
                  AND u.email IS NOT NULL
                  AND l.vector IS NOT NULL
            """)
            items = cur.fetchall()
            for item in items:
                target_direction = "found" if item["direction"] == "lost" else "lost"
                # Actual vector search for matches > 0.8
                cur.execute("""
                    SELECT id, item_name, 1 - (vector <=> %s::vector) AS similarity
                    FROM lost_items
                    WHERE direction = %s
                      AND status = 'active'
                      AND id <> %s
                      AND 1 - (vector <=> %s::vector) > 0.8
                    ORDER BY similarity DESC LIMIT 5
                """, (item["vector"], target_direction, item["id"], item["vector"]))
                matches = cur.fetchall()
                if matches:
                    await send_match_email(
                        to_email=item['email'],
                        item_name=item['item_name'],
                        contact_person=item['contact_person'],
                        matched_items=matches
                    )
            
            cur.close()
            release_db_connection(conn)
        except Exception as e:
            logging.error(f"Error in periodic_email_matcher: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 上传文件配置
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# 挂载上传目录为静态文件服务
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.post("/api/upload")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """上传图片，返回可访问的 URL"""
    verify_csrf_origin(request)

    # 校验文件扩展名（统一小写）
    original_name = file.filename or "unknown"
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}。允许的类型: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 校验 MIME 类型
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file.content_type}"
        )

    # 生成唯一文件名
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # 保存文件
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"文件大小超过 {MAX_FILE_SIZE // 1024 // 1024}MB 限制")

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(contents)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="文件保存失败")

    # 返回相对路径 — 兼容开发代理和生产反向代理
    file_url = f"/uploads/{safe_name}"

    return {"url": file_url, "filename": safe_name}


@app.get("/api/auth/login")
def auth_login(next: Optional[str] = "/"):
    state = new_state()
    response = RedirectResponse(make_login_url(state), status_code=302)
    response.set_cookie(
        STATE_COOKIE,
        state,
        max_age=OAUTH_STATE_EXPIRE_SECONDS,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    response.set_cookie(
        NEXT_COOKIE,
        next if next and next.startswith("/") and not next.startswith("//") else "/",
        max_age=OAUTH_STATE_EXPIRE_SECONDS,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    return response


@app.get("/api/auth/callback")
async def auth_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None):
    expected_state = request.cookies.get(STATE_COOKIE)
    if not code or not state or not expected_state or state != expected_state:
        return RedirectResponse(safe_frontend_redirect("/?auth_error=oauth_state_invalid"), status_code=302)

    token_payload = await exchange_code_for_token(code)
    userinfo = await get_casdoor_userinfo(token_payload["access_token"])
    user = get_or_create_user(userinfo)
    session_token = create_session_token(user["id"])

    redirect_to = safe_frontend_redirect(request.cookies.get(NEXT_COOKIE))
    response = RedirectResponse(redirect_to, status_code=302)
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=24 * 60 * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    response.delete_cookie(STATE_COOKIE)
    response.delete_cookie(NEXT_COOKIE)
    return response


@app.get("/api/auth/me")
def auth_me(request: Request):
    return {"user": get_current_user(request)}


@app.post("/api/auth/logout")
def auth_logout(request: Request):
    verify_csrf_origin(request)
    response = JSONResponse({"message": "已退出登录"})
    response.delete_cookie(SESSION_COOKIE)
    return response


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    qq: Optional[str] = None
    email: Optional[str] = None



# 数据库向量列维度（需与 pgvector column 定义一致）
VECTOR_DIM = int(os.environ.get("VECTOR_DIM", "1536"))


def _vector_str(values: list[float]) -> str:
    trimmed = values[:VECTOR_DIM]
    return "[" + ",".join(str(v) for v in trimmed) + "]"


def _normalize_vector(values: list[float]) -> list[float]:
    norm = sum(v * v for v in values) ** 0.5
    if norm == 0:
        return values
    return [v / norm for v in values]


def _average_vectors(vectors: list[list[float]]) -> list[float]:
    min_dim = min(len(v) for v in vectors)
    averaged = [
        sum(vector[i] for vector in vectors) / len(vectors)
        for i in range(min_dim)
    ]
    return _normalize_vector(averaged)


def _image_url_to_path(url: str) -> Optional[str]:
    if not url:
        return None

    parsed = urlparse(url.strip())
    path = unquote(parsed.path if parsed.scheme else url.strip())

    if path.startswith("/uploads/"):
        candidate = os.path.join(UPLOAD_DIR, path.removeprefix("/uploads/"))
    elif path.startswith("uploads/"):
        candidate = os.path.join(UPLOAD_DIR, path.removeprefix("uploads/"))
    elif os.path.isabs(path):
        candidate = path
    else:
        candidate = os.path.join(UPLOAD_DIR, path)

    candidate = os.path.abspath(candidate)
    upload_root = os.path.abspath(UPLOAD_DIR)
    if not candidate.startswith(upload_root + os.sep):
        return None
    return candidate if os.path.isfile(candidate) else None


def _iter_image_paths(image_url: Optional[str]) -> list[str]:
    if not image_url:
        return []
    paths = []
    for raw_url in image_url.split(","):
        path = _image_url_to_path(raw_url)
        if path:
            paths.append(path)
    return paths


@lru_cache(maxsize=128)
def _build_vector(item_name: str, location: Optional[str] = None, lost_time: Optional[str] = None, description: Optional[str] = None, image_url: Optional[str] = None) -> Optional[str]:
    try:
        image_paths = _iter_image_paths(image_url)
        # Parse or format lost_time if necessary (assuming it is string or datetime)
        time_str = str(lost_time) if lost_time else ""
        vec = encode_multimodal(item_name, location or "", time_str, description or "", image_paths)
        return _vector_str(vec)
    except Exception as e:
        import logging
        logging.error(f"Error building multimodal vector: {e}")
        return None





def serialize_row(row):
    """将 DictCursor 行转为 JSON 兼容的 dict（datetime → str）"""
    if row is None:
        return None
    result = dict(row)
    for key, value in result.items():
        if hasattr(value, 'isoformat'):
            result[key] = value.isoformat()
    return result


def none_if_empty(val):
    """将空字符串转为 None，避免 PostgreSQL 解析空字符串报错"""
    return val if val not in (None, '') else None


def _get_claim_item_ids_for_user(cur, user: Optional[dict]) -> set[int]:
    if not user:
        return set()
    try:
        cur.execute(
            """SELECT item_id
               FROM claim_requests
               WHERE requester_user_id = %s OR owner_user_id = %s""",
            (user["id"], user["id"]),
        )
        return {row[0] for row in cur.fetchall()}
    except psycopg2.errors.UndefinedTable:
        cur.connection.rollback()
        return set()


def _can_view_item_contact(item: dict, user: Optional[dict], claim_item_ids: Optional[set[int]] = None) -> bool:
    if not item:
        return False
    visibility = item.get("contact_visibility") or "private"
    if visibility == "public":
        return True
    if not user:
        return False
    if user.get("role") == "admin" or item.get("user_id") == user.get("id"):
        return True
    if visibility == "logged_in":
        return True
    if claim_item_ids and item.get("id") in claim_item_ids:
        return True
    return False


def serialize_item_for_user(row, user: Optional[dict], claim_item_ids: Optional[set[int]] = None):
    item = serialize_row(row)
    if item is None:
        return None
    if not _can_view_item_contact(item, user, claim_item_ids):
        item["contact_person"] = "匿名"
        item["contact_phone"] = None
        item["contact_qq"] = None
        item["contact_email"] = None
        item["storage_location"] = None
    return item


DIRECTION_ALIASES = {
    "lost": "lost",
    "find_item": "lost",
    "找物": "lost",
    "寻物": "lost",
    "found": "found",
    "find_owner": "found",
    "找主": "found",
    "招领": "found",
}

STATUS_ALIASES = {
    "active": "active",
    "pending": "active",
    "待匹配": "active",
    "待解决": "active",
    "recovered": "recovered",
    "resolved": "recovered",
    "matched": "recovered",
    "closed": "recovered",
    "已找回": "recovered",
    "已完成": "recovered",
    "expired": "expired",
    "过期": "expired",
}


def _clean_state_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _coerce_direction(value: Optional[str]) -> Optional[str]:
    value = _clean_state_value(value)
    if value is None:
        return None
    return DIRECTION_ALIASES.get(value)


def _coerce_status(value: Optional[str]) -> Optional[str]:
    value = _clean_state_value(value)
    if value is None:
        return None
    return STATUS_ALIASES.get(value)


def _resolve_create_state(
    direction: Optional[str] = None,
    status: Optional[str] = None,
    post_type: Optional[str] = None,
) -> tuple[str, str]:
    resolved_direction = _coerce_direction(direction)
    if direction is not None and resolved_direction is None:
        raise HTTPException(status_code=400, detail="无效发布方向，仅支持 lost/found 或 找物/找主")

    post_type_direction = _coerce_direction(post_type)
    if post_type is not None and post_type_direction is None:
        raise HTTPException(status_code=400, detail="无效旧版 post_type，仅支持 lost/found")
    if resolved_direction is not None and post_type_direction is not None and resolved_direction != post_type_direction:
        raise HTTPException(status_code=400, detail="direction 与 post_type 冲突")
    if resolved_direction is None:
        resolved_direction = post_type_direction

    status_as_direction = _coerce_direction(status)
    resolved_status = _coerce_status(status)
    if status is not None and status_as_direction is None and resolved_status is None:
        raise HTTPException(status_code=400, detail="无效状态，仅支持 active/recovered/expired 或旧值 lost/found/pending/resolved")

    if resolved_direction is None and status_as_direction is not None:
        resolved_direction = status_as_direction
    if resolved_direction is None:
        resolved_direction = "lost"
    if resolved_status is None:
        resolved_status = "active"

    return resolved_direction, resolved_status


def _append_item_filters(
    where_clause: str,
    params: list,
    *,
    status: Optional[str] = None,
    direction: Optional[str] = None,
    post_type: Optional[str] = None,
    item_type: Optional[str] = None,
) -> str:
    if item_type:
        where_clause += " AND item_type = %s"
        params.append(item_type)

    resolved_direction = _coerce_direction(direction)
    if direction is not None and resolved_direction is None:
        raise HTTPException(status_code=400, detail="无效发布方向筛选")

    post_type_direction = _coerce_direction(post_type)
    if post_type is not None and post_type_direction is None:
        raise HTTPException(status_code=400, detail="无效旧版 post_type 筛选")
    if resolved_direction is not None and post_type_direction is not None and resolved_direction != post_type_direction:
        raise HTTPException(status_code=400, detail="direction 与 post_type 筛选冲突")
    if resolved_direction is None:
        resolved_direction = post_type_direction

    status_as_direction = _coerce_direction(status)
    resolved_status = _coerce_status(status)
    if status is not None and status_as_direction is None and resolved_status is None:
        raise HTTPException(status_code=400, detail="无效状态筛选")

    if status_as_direction is not None:
        if resolved_direction is not None and resolved_direction != status_as_direction:
            raise HTTPException(status_code=400, detail="发布方向与旧版 status 筛选冲突")
        resolved_direction = status_as_direction
        resolved_status = "active"

    if resolved_direction is not None:
        where_clause += " AND direction = %s"
        params.append(resolved_direction)
    if resolved_status is not None:
        where_clause += " AND status = %s"
        params.append(resolved_status)

    return where_clause


def _append_state_update(update_fields: list[str], params: list, direction: Optional[str], status: Optional[str], post_type: Optional[str]) -> None:
    resolved_direction = _coerce_direction(direction)
    if direction is not None and resolved_direction is None:
        raise HTTPException(status_code=400, detail="无效发布方向，仅支持 lost/found 或 找物/找主")

    post_type_direction = _coerce_direction(post_type)
    if post_type is not None and post_type_direction is None:
        raise HTTPException(status_code=400, detail="无效旧版 post_type，仅支持 lost/found")
    if resolved_direction is not None and post_type_direction is not None and resolved_direction != post_type_direction:
        raise HTTPException(status_code=400, detail="direction 与 post_type 更新冲突")
    if resolved_direction is None:
        resolved_direction = post_type_direction

    status_as_direction = _coerce_direction(status)
    resolved_status = _coerce_status(status)
    if status is not None and status_as_direction is None and resolved_status is None:
        raise HTTPException(status_code=400, detail="无效状态，仅支持 active/recovered/expired 或旧值 lost/found/pending/resolved")

    if status_as_direction is not None:
        if resolved_direction is not None and resolved_direction != status_as_direction:
            raise HTTPException(status_code=400, detail="发布方向与旧版 status 更新冲突")
        resolved_direction = status_as_direction
        resolved_status = "active"

    if resolved_direction is not None:
        update_fields.append("direction = %s")
        params.append(resolved_direction)
    if resolved_status is not None:
        update_fields.append("status = %s")
        params.append(resolved_status)


class UserCreate(BaseModel):
    student_id: str
    name: str
    phone: Optional[str] = None
    qq: Optional[str] = None
    email: Optional[str] = None

class UserUpdate(BaseModel):
    role: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    qq: Optional[str] = None
    email: Optional[str] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    qq: Optional[str] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    student_id: str
    name: str
    phone: Optional[str] = None
    qq: Optional[str] = None
    email: Optional[str] = None
    role: str
    created_at: str
    casdoor_name: Optional[str] = None

class LostItemCreate(BaseModel):
    item_name: str
    item_type: Optional[str] = None
    direction: Optional[str] = None
    post_type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    storage_location: Optional[str] = None
    lost_time: Optional[str] = None
    status: Optional[str] = None
    contact_visibility: Optional[str] = None
    image_url: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_qq: Optional[str] = None
    contact_email: Optional[str] = None

class LostItemUpdate(BaseModel):
    item_name: Optional[str] = None
    item_type: Optional[str] = None
    direction: Optional[str] = None
    post_type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    storage_location: Optional[str] = None
    found_time: Optional[str] = None
    status: Optional[str] = None
    contact_visibility: Optional[str] = None
    image_url: Optional[str] = None
    contact_email: Optional[str] = None

class LostItemResponse(BaseModel):
    id: int
    item_name: str
    item_type: Optional[str] = None
    direction: str
    description: Optional[str] = None
    location: Optional[str] = None
    storage_location: Optional[str] = None
    lost_time: Optional[str] = None
    found_time: Optional[str] = None
    status: str
    contact_visibility: str
    image_url: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_qq: Optional[str] = None
    contact_email: Optional[str] = None
    user_id: Optional[int] = None
    created_at: str
    updated_at: str

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: Optional[str] = None
    notification_type: Optional[str] = None
    related_item_id: Optional[int] = None
    link_url: Optional[str] = None
    is_read: bool
    created_at: str

class ClaimRequestCreate(BaseModel):
    requester_name: str
    requester_contact: str
    message: Optional[str] = None

class ClaimRequestResponse(BaseModel):
    id: int
    item_id: int
    requester_user_id: int
    owner_user_id: Optional[int] = None
    request_type: str
    requester_name: str
    requester_contact: str
    message: Optional[str] = None
    status: str
    created_at: str
    item_name: Optional[str] = None
    item_direction: Optional[str] = None
    requester_user_name: Optional[str] = None
    owner_user_name: Optional[str] = None


def _coerce_contact_visibility(value: Optional[str]) -> str:
    if value is None or value == "":
        return "private"
    if value not in ("private", "logged_in", "claimed", "public"):
        raise HTTPException(status_code=400, detail="无效联系方式可见性")
    return value


def _insert_notification(cur, user_id: Optional[int], title: str, message: str, notification_type: str, related_item_id: Optional[int] = None):
    if not user_id:
        return
    cur.execute(
        """INSERT INTO notifications
           (user_id, title, message, notification_type, related_item_id, link_url)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (user_id, title, message, notification_type, related_item_id, f"/lost/{related_item_id}" if related_item_id else None),
    )

@app.get("/api/me", response_model=UserResponse)
def get_me(request: Request):
    return get_current_user(request)

@app.put("/api/me", response_model=UserResponse)
def update_me(update: UserProfileUpdate, request: Request):
    current_user = get_current_user(request)
    verify_csrf_origin(request)

    update_fields = []
    params = []
    if update.name is not None:
        nickname = update.name.strip()
        if not nickname:
            raise HTTPException(status_code=400, detail="昵称不能为空")
        update_fields.append("name = %s")
        params.append(nickname)
    if update.phone is not None:
        update_fields.append("phone = %s")
        params.append(none_if_empty(update.phone))
    if update.qq is not None:
        update_fields.append("qq = %s")
        params.append(none_if_empty(update.qq))
    if update.email is not None:
        update_fields.append("email = %s")
        params.append(none_if_empty(update.email))

    if not update_fields:
        raise HTTPException(status_code=400, detail="没有要更新的字段")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        params.append(current_user["id"])
        query = "UPDATE users SET " + ", ".join(update_fields) + " WHERE id = %s RETURNING *"
        cur.execute(query, params)
        conn.commit()
        return serialize_row(cur.fetchone())
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"更新个人资料失败: {e}")
    finally:
        cur.close()
        release_db_connection(conn)


@app.get("/api/notifications", response_model=List[NotificationResponse])
def get_notifications(request: Request, unread_only: bool = False, limit: int = 20):
    current_user = get_current_user(request)
    limit = max(1, min(limit, 100))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        where_clause = "WHERE user_id = %s"
        params = [current_user["id"]]
        if unread_only:
            where_clause += " AND is_read = FALSE"
        params.append(limit)
        cur.execute(
            f"""SELECT id, title, message, notification_type, related_item_id, link_url, is_read, created_at
                FROM notifications
                {where_clause}
                ORDER BY created_at DESC
                LIMIT %s""",
            params,
        )
        return [serialize_row(row) for row in cur.fetchall()]
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        return []
    finally:
        cur.close()
        release_db_connection(conn)


@app.get("/api/notifications/unread-count")
def get_unread_notification_count(request: Request):
    current_user = get_current_user(request)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE", (current_user["id"],))
        return {"unread_count": cur.fetchone()[0]}
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        return {"unread_count": 0}
    finally:
        cur.close()
        release_db_connection(conn)


@app.put("/api/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: int, request: Request):
    current_user = get_current_user(request)
    verify_csrf_origin(request)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(
            """UPDATE notifications
               SET is_read = TRUE
               WHERE id = %s AND user_id = %s
               RETURNING id, title, message, notification_type, related_item_id, link_url, is_read, created_at""",
            (notification_id, current_user["id"]),
        )
        row = cur.fetchone()
        conn.commit()
        if not row:
            raise HTTPException(status_code=404, detail="通知不存在")
        return serialize_row(row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"更新通知失败: {e}")
    finally:
        cur.close()
        release_db_connection(conn)


@app.post("/api/lost-items/{item_id}/claim", response_model=ClaimRequestResponse)
def create_claim_request(item_id: int, claim: ClaimRequestCreate, request: Request):
    current_user = get_current_user(request)
    verify_csrf_origin(request)
    requester_name = claim.requester_name.strip()
    requester_contact = claim.requester_contact.strip()
    if not requester_name or not requester_contact:
        raise HTTPException(status_code=400, detail="请填写称呼和联系方式")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(
            """SELECT id, item_name, direction, status, user_id, contact_person
               FROM lost_items
               WHERE id = %s
               FOR UPDATE""",
            (item_id,),
        )
        item = cur.fetchone()
        if not item:
            raise HTTPException(status_code=404, detail="物品不存在")
        if item["status"] != "active":
            raise HTTPException(status_code=400, detail="该物品当前不可申请")
        if item["user_id"] == current_user["id"]:
            raise HTTPException(status_code=400, detail="不能申请自己发布的物品")
        if current_user.get("role") != "admin":
            cur.execute(
                """SELECT COUNT(*)
                   FROM claim_requests
                   WHERE requester_user_id = %s
                     AND created_at > CURRENT_TIMESTAMP - INTERVAL '10 minutes'""",
                (current_user["id"],),
            )
            if cur.fetchone()[0] >= 5:
                raise HTTPException(status_code=429, detail="申请过于频繁，请稍后再试")

        request_type = "claim" if item["direction"] == "found" else "contact"
        request_status = "completed" if request_type == "claim" else "submitted"
        owner_user_id = item["user_id"]
        cur.execute(
            """INSERT INTO claim_requests
               (item_id, requester_user_id, owner_user_id, request_type, requester_name, requester_contact, message, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING *""",
            (
                item_id,
                current_user["id"],
                owner_user_id,
                request_type,
                requester_name,
                requester_contact,
                none_if_empty(claim.message),
                request_status,
            ),
        )
        claim_row = cur.fetchone()

        if request_type == "claim":
            cur.execute(
                "UPDATE lost_items SET status = 'recovered', updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (item_id,),
            )
            _insert_notification(
                cur,
                owner_user_id,
                "有人认领了你发布的物品",
                f"{requester_name} 认领了「{item['item_name']}」，联系方式：{requester_contact}",
                "claim",
                item_id,
            )
            _insert_notification(
                cur,
                current_user["id"],
                "认领申请已提交",
                f"你已认领「{item['item_name']}」，请按页面联系方式完成线下核验。",
                "claim",
                item_id,
            )
        else:
            _insert_notification(
                cur,
                owner_user_id,
                "有人可能捡到了你的物品",
                f"{requester_name} 表示可能捡到了「{item['item_name']}」，联系方式：{requester_contact}",
                "contact",
                item_id,
            )
            _insert_notification(
                cur,
                current_user["id"],
                "联系申请已提交",
                f"你已向「{item['item_name']}」的发布者发送联系申请。",
                "contact",
                item_id,
            )

        conn.commit()
        result = serialize_row(claim_row)
        result["item_name"] = item["item_name"]
        result["item_direction"] = item["direction"]
        result["requester_user_name"] = current_user["name"]
        return result
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="你已经提交过申请")
    except HTTPException:
        conn.rollback()
        raise
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        raise HTTPException(status_code=500, detail="认领申请表尚未初始化，请先执行数据库迁移")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"提交申请失败: {e}")
    finally:
        cur.close()
        release_db_connection(conn)


@app.get("/api/me/claims", response_model=List[ClaimRequestResponse])
def get_my_claim_requests(request: Request):
    current_user = get_current_user(request)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(
            """SELECT cr.*, li.item_name, li.direction AS item_direction,
                      ru.name AS requester_user_name, ou.name AS owner_user_name
               FROM claim_requests cr
               JOIN lost_items li ON li.id = cr.item_id
               JOIN users ru ON ru.id = cr.requester_user_id
               LEFT JOIN users ou ON ou.id = cr.owner_user_id
               WHERE cr.requester_user_id = %s OR cr.owner_user_id = %s
               ORDER BY cr.created_at DESC""",
            (current_user["id"], current_user["id"]),
        )
        return [serialize_row(row) for row in cur.fetchall()]
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        return []
    finally:
        cur.close()
        release_db_connection(conn)


@app.get("/api/claim-requests", response_model=List[ClaimRequestResponse])
def get_claim_requests(request: Request, limit: int = 100):
    require_admin(request)
    limit = max(1, min(limit, 500))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(
            """SELECT cr.*, li.item_name, li.direction AS item_direction,
                      ru.name AS requester_user_name, ou.name AS owner_user_name
               FROM claim_requests cr
               JOIN lost_items li ON li.id = cr.item_id
               JOIN users ru ON ru.id = cr.requester_user_id
               LEFT JOIN users ou ON ou.id = cr.owner_user_id
               ORDER BY cr.created_at DESC
               LIMIT %s""",
            (limit,),
        )
        return [serialize_row(row) for row in cur.fetchall()]
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        return []
    finally:
        cur.close()
        release_db_connection(conn)


@app.get("/api/me/items")
def get_my_lost_items(
    request: Request,
    status: Optional[str] = None,
    direction: Optional[str] = None,
    post_type: Optional[str] = None,
    item_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    current_user = get_current_user(request)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    where_clause = "WHERE user_id = %s"
    params = [current_user["id"]]

    where_clause = _append_item_filters(
        where_clause,
        params,
        status=status,
        direction=direction,
        post_type=post_type,
        item_type=item_type,
    )

    cur.execute(f"SELECT COUNT(*) as total FROM lost_items {where_clause}", params)
    total = cur.fetchone()['total']

    query_params = params + [page_size, (page - 1) * page_size]
    cur.execute(
        f"SELECT * FROM lost_items {where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s",
        query_params
    )
    items = cur.fetchall()
    cur.close()
    release_db_connection(conn)

    return {
        "items": [serialize_row(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@app.get("/api/users", response_model=List[UserResponse])
def get_users(request: Request):
    require_admin(request)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    cur.close()
    release_db_connection(conn)
    return [serialize_row(u) for u in users]

@app.post("/api/users", response_model=UserResponse)
def create_user(user: UserCreate, request: Request):
    require_admin(request)
    verify_csrf_origin(request)
    raise HTTPException(status_code=410, detail="用户由 Casdoor 登录自动创建，请不要手动创建本地用户")

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, request: Request):
    current_user = get_current_user(request)
    if current_user["id"] != user_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="只能查看自己的用户信息")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    release_db_connection(conn)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return serialize_row(user)

@app.put("/api/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, update: UserUpdate, request: Request):
    """管理员更新用户信息（角色/姓名等）"""
    current_user = require_admin(request)
    verify_csrf_origin(request)
    if current_user["id"] == user_id and update.role == "user":
        raise HTTPException(status_code=400, detail="不能降级当前登录的管理员账号")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="用户不存在")

        update_fields = []
        params = []
        if update.role is not None:
            if update.role not in ("admin", "user"):
                raise HTTPException(status_code=400, detail="无效角色，仅支持 admin / user")
            update_fields.append("role = %s")
            params.append(update.role)
        if update.name is not None:
            update_fields.append("name = %s")
            params.append(update.name)
        if update.phone is not None:
            update_fields.append("phone = %s")
            params.append(none_if_empty(update.phone))
        if update.qq is not None:
            update_fields.append("qq = %s")
            params.append(none_if_empty(update.qq))
        if update.email is not None:
            update_fields.append("email = %s")
            params.append(none_if_empty(update.email))

        if not update_fields:
            raise HTTPException(status_code=400, detail="没有要更新的字段")

        params.append(user_id)
        query = "UPDATE users SET " + ", ".join(update_fields) + " WHERE id = %s RETURNING *"
        cur.execute(query, params)
        conn.commit()
        return serialize_row(cur.fetchone())
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"更新用户失败: {e}")
    finally:
        cur.close()
        release_db_connection(conn)



@app.get("/api/lost-items")
def get_lost_items(
    request: Request,
    status: Optional[str] = None,
    direction: Optional[str] = None,
    post_type: Optional[str] = None,
    item_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # 构建查询条件
    where_clause = "WHERE 1=1"
    params = []
    
    where_clause = _append_item_filters(
        where_clause,
        params,
        status=status,
        direction=direction,
        post_type=post_type,
        item_type=item_type,
    )
    
    # 查询总数
    count_query = f"SELECT COUNT(*) as total FROM lost_items {where_clause}"
    cur.execute(count_query, params)
    total = cur.fetchone()['total']
    
    # 查询分页数据
    query = f"SELECT * FROM lost_items {where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([page_size, (page - 1) * page_size])
    
    cur.execute(query, params)
    items = cur.fetchall()
    current_user = get_optional_user(request)
    claim_item_ids = _get_claim_item_ids_for_user(cur, current_user)
    cur.close()
    release_db_connection(conn)
    
    return {
        "items": [serialize_item_for_user(item, current_user, claim_item_ids) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }

class MatchCheckRequest(LostItemCreate):
    pass

@app.post("/api/match-check")
def match_check(item: MatchCheckRequest, request: Request, limit: int = 5):
    direction, _ = _resolve_create_state(item.direction, item.status, item.post_type)
    vector = _build_vector(item.item_name, item.location, str(item.lost_time) if item.lost_time else "", item.description, item.image_url)
    if not vector:
        return {"results": []}

    target_direction = "found" if direction == "lost" else "lost"
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(
            """SELECT *, 1 - (vector <=> %s::vector) AS similarity
               FROM lost_items
               WHERE vector IS NOT NULL
                 AND direction = %s
                 AND status = 'active'
               ORDER BY vector <=> %s::vector
               LIMIT %s""",
            (vector, target_direction, vector, limit)
        )
        items = cur.fetchall()
        current_user = get_optional_user(request)
        claim_item_ids = _get_claim_item_ids_for_user(cur, current_user)
        # Only return high similarity items? For now return top 5
        return {"results": [serialize_item_for_user(row, current_user, claim_item_ids) for row in items]}
    finally:
        cur.close()
        release_db_connection(conn)

@app.post("/api/lost-items", response_model=LostItemResponse)
def create_lost_item(item: LostItemCreate, request: Request):
    verify_csrf_origin(request)
    direction, status = _resolve_create_state(item.direction, item.status, item.post_type)
    current_user = get_optional_user(request)
    has_contact = any(none_if_empty(value) for value in (item.contact_phone, item.contact_qq, item.contact_email))
    if direction == "lost" and not current_user:
        raise HTTPException(status_code=401, detail="发布寻物信息需要先登录")
    if direction == "lost" and not has_contact:
        raise HTTPException(status_code=400, detail="发布寻物信息至少需要填写一种联系方式")
    if direction == "found" and not current_user and has_contact:
        raise HTTPException(status_code=401, detail="匿名招领不能填写联系方式，请登录后实名发布")

    if direction == "found" and not current_user:
        contact_visibility = "private"
    elif item.contact_visibility is not None:
        contact_visibility = _coerce_contact_visibility(item.contact_visibility)
    elif direction == "lost":
        contact_visibility = "logged_in"
    elif has_contact:
        contact_visibility = "claimed"
    else:
        contact_visibility = "private"
    contact_person = none_if_empty(item.contact_person)
    if not contact_person:
        contact_person = current_user["name"] if current_user else "匿名"

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    vector = _build_vector(item.item_name, item.location, str(item.lost_time) if item.lost_time else "", item.description, item.image_url)
    try:
        # 显式获取下一个 ID（序列权限变通方案）
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM lost_items")
        next_id = cur.fetchone()[0]

        cur.execute(
            """INSERT INTO lost_items
               (id, item_name, item_type, description, location, storage_location, lost_time, direction, status, contact_visibility,
                image_url, contact_person, contact_phone, contact_qq, contact_email, user_id, vector)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector) RETURNING *""",
            (next_id, item.item_name, none_if_empty(item.item_type),
             none_if_empty(item.description), none_if_empty(item.location),
             none_if_empty(item.storage_location), none_if_empty(item.lost_time), direction, status, contact_visibility,
             none_if_empty(item.image_url), contact_person,
             none_if_empty(item.contact_phone), none_if_empty(item.contact_qq), none_if_empty(item.contact_email),
             current_user["id"] if current_user else None,
             none_if_empty(vector))
        )
        conn.commit()
        new_item = cur.fetchone()
        return serialize_row(new_item)
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"创建失物信息失败: {e}")
    finally:
        cur.close()
        release_db_connection(conn)

@app.get("/api/lost-items/{item_id}", response_model=LostItemResponse)
def get_lost_item(item_id: int, request: Request):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM lost_items WHERE id = %s", (item_id,))
    item = cur.fetchone()
    current_user = get_optional_user(request)
    claim_item_ids = _get_claim_item_ids_for_user(cur, current_user)
    cur.close()
    release_db_connection(conn)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    return serialize_item_for_user(item, current_user, claim_item_ids)

@app.put("/api/lost-items/{item_id}", response_model=LostItemResponse)
def update_lost_item(item_id: int, item: LostItemUpdate, request: Request):
    current_user = get_current_user(request)
    verify_csrf_origin(request)
    assert_owner_or_admin(item_id, current_user)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        update_fields = []
        params = []
        
        if item.item_name is not None:
            update_fields.append("item_name = %s")
            params.append(none_if_empty(item.item_name))
        if item.item_type is not None:
            update_fields.append("item_type = %s")
            params.append(none_if_empty(item.item_type))
        if item.description is not None:
            update_fields.append("description = %s")
            params.append(none_if_empty(item.description))
        if item.location is not None:
            update_fields.append("location = %s")
            params.append(none_if_empty(item.location))
        if item.storage_location is not None:
            update_fields.append("storage_location = %s")
            params.append(none_if_empty(item.storage_location))
        if item.found_time is not None:
            update_fields.append("found_time = %s")
            params.append(none_if_empty(item.found_time))
        _append_state_update(update_fields, params, item.direction, item.status, item.post_type)
        if item.contact_visibility is not None:
            update_fields.append("contact_visibility = %s")
            params.append(_coerce_contact_visibility(item.contact_visibility))
        if item.contact_email is not None:
            update_fields.append("contact_email = %s")
            params.append(none_if_empty(item.contact_email))
        if item.image_url is not None:
            update_fields.append("image_url = %s")
            params.append(none_if_empty(item.image_url))
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="没有要更新的字段")

        if item.item_name or item.description or item.location or item.found_time or item.image_url:
            cur.execute(
                "SELECT item_name, location, lost_time, description, image_url FROM lost_items WHERE id = %s",
                (item_id,),
            )
            row = cur.fetchone()
            if row:
                new_name = item.item_name or row["item_name"]
                new_location = item.location or row["location"]
                new_time = item.found_time or row["lost_time"]
                new_desc = item.description or row["description"]
                new_img = item.image_url or row["image_url"]
                vector = _build_vector(new_name, new_location, str(new_time) if new_time else "", new_desc, new_img)
                update_fields.append("vector = %s::vector")
                params.append(vector)

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(item_id)
        
        query = "UPDATE lost_items SET " + ", ".join(update_fields) + " WHERE id = %s RETURNING *"
        cur.execute(query, params)
        conn.commit()
        updated_item = cur.fetchone()
        
        if not updated_item:
            raise HTTPException(status_code=404, detail="物品不存在")
        
        return serialize_row(updated_item)
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="更新失物信息失败")
    finally:
        cur.close()
        release_db_connection(conn)

@app.delete("/api/lost-items/{item_id}")
def delete_lost_item(item_id: int, request: Request):
    current_user = get_current_user(request)
    verify_csrf_origin(request)
    assert_owner_or_admin(item_id, current_user)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM lost_items WHERE id = %s", (item_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="物品不存在")
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="删除失物信息失败")
    finally:
        cur.close()
        release_db_connection(conn)

@app.get("/api/search")
def search_lost_items(
    request: Request,
    query: str = Query(..., min_length=1),
    item_type: Optional[str] = None,
    status: Optional[str] = None,
    direction: Optional[str] = None,
    post_type: Optional[str] = None,
    limit: int = 10
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    search_query = "SELECT * FROM lost_items WHERE 1=1"
    params = []
    
    search_query = _append_item_filters(
        search_query,
        params,
        status=status,
        direction=direction,
        post_type=post_type,
        item_type=item_type,
    )
    
    search_query += " AND (item_name ILIKE %s OR description ILIKE %s OR location ILIKE %s)"
    params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    
    search_query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    
    cur.execute(search_query, params)
    items = cur.fetchall()
    current_user = get_optional_user(request)
    claim_item_ids = _get_claim_item_ids_for_user(cur, current_user)
    cur.close()
    release_db_connection(conn)
    
    return {"results": [serialize_item_for_user(item, current_user, claim_item_ids) for item in items]}


@app.get("/api/semantic-search")
def semantic_search(
    request: Request,
    query: str = Query(..., min_length=1),
    item_type: Optional[str] = None,
    status: Optional[str] = None,
    direction: Optional[str] = None,
    post_type: Optional[str] = None,
    limit: int = 10
):
    try:
        vec = encode_text(query)
    except Exception:
        raise HTTPException(status_code=500, detail="向量模型未就绪")

    vector_str = _vector_str(vec)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        where_clause = "WHERE vector IS NOT NULL"
        params = [vector_str]
        where_clause = _append_item_filters(
            where_clause,
            params,
            status=status,
            direction=direction,
            post_type=post_type,
            item_type=item_type,
        )
        params.extend([vector_str, limit])
        cur.execute(
            f"""SELECT *, 1 - (vector <=> %s::vector) AS similarity
                FROM lost_items
                {where_clause}
                ORDER BY vector <=> %s::vector
                LIMIT %s""",
            params
        )
        items = cur.fetchall()
        current_user = get_optional_user(request)
        claim_item_ids = _get_claim_item_ids_for_user(cur, current_user)
        return {"results": [serialize_item_for_user(item, current_user, claim_item_ids) for item in items]}
    finally:
        cur.close()
        release_db_connection(conn)


@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM lost_items WHERE direction = 'lost' AND status = 'active'")
    lost_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM lost_items WHERE direction = 'found' AND status = 'active'")
    found_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM lost_items WHERE status = 'recovered'")
    recovered_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM lost_items WHERE status = 'expired'")
    expired_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM lost_items")
    total_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    
    cur.close()
    release_db_connection(conn)
    
    return {
        "total_items": total_count,
        "lost_count": lost_count,
        "found_count": found_count,
        "recovered_count": recovered_count,
        "expired_count": expired_count,
        "user_count": user_count
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
