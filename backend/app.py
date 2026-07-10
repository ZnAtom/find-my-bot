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
from urllib.parse import unquote, urlparse
from auth import (
    COOKIE_SECURE,
    NEXT_COOKIE,
    SESSION_COOKIE,
    STATE_COOKIE,
    assert_owner_or_admin,
    create_session_token,
    exchange_code_for_token,
    get_casdoor_userinfo,
    get_current_user,
    get_or_create_user,
    make_login_url,
    new_state,
    require_admin,
    safe_frontend_redirect,
    verify_csrf_origin,
)
from embedding import encode_text, encode_image

app = FastAPI(title="校园失物招领 API", version="1.0.0")


CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]

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
    get_current_user(request)
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

        with open(file_path, "wb") as f:
            f.write(contents)
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
        max_age=600,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    response.set_cookie(
        NEXT_COOKIE,
        next if next and next.startswith("/") and not next.startswith("//") else "/",
        max_age=600,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    return response


@app.get("/api/auth/callback")
async def auth_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None):
    expected_state = request.cookies.get(STATE_COOKIE)
    if not code or not state or not expected_state or state != expected_state:
        raise HTTPException(status_code=400, detail="OAuth 回调状态无效")

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


DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "lostfound"),
    "user": os.environ.get("DB_USER", "appuser"),
    "password": os.environ.get("DB_PASSWORD", "password"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432")
}

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


def _build_vector(item_name: str, description: Optional[str] = None, image_url: Optional[str] = None) -> Optional[str]:
    text_parts = [item_name]
    if description:
        text_parts.append(description)
    text = " ".join(text_parts)
    vectors = []

    try:
        if text.strip():
            vectors.append(encode_text(text))

        for image_path in _iter_image_paths(image_url):
            try:
                vectors.append(encode_image(image_path))
            except Exception:
                continue

        if not vectors:
            return None
        return _vector_str(_average_vectors(vectors))
    except Exception:
        return None


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


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
    description: Optional[str] = None
    location: Optional[str] = None
    lost_time: Optional[str] = None
    status: Optional[str] = "lost"
    image_url: Optional[str] = None
    contact_person: str
    contact_phone: Optional[str] = None
    contact_qq: Optional[str] = None

class LostItemUpdate(BaseModel):
    item_name: Optional[str] = None
    item_type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    found_time: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None

class LostItemResponse(BaseModel):
    id: int
    item_name: str
    item_type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    lost_time: Optional[str] = None
    found_time: Optional[str] = None
    status: str
    image_url: Optional[str] = None
    contact_person: str
    contact_phone: Optional[str] = None
    contact_qq: Optional[str] = None
    user_id: Optional[int] = None
    created_at: str
    updated_at: str

@app.get("/api/users", response_model=List[UserResponse])
def get_users(request: Request):
    require_admin(request)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
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
    conn.close()
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
        conn.close()



@app.get("/api/lost-items")
def get_lost_items(
    status: Optional[str] = None,
    item_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # 构建查询条件
    where_clause = "WHERE 1=1"
    params = []
    
    if status:
        where_clause += " AND status = %s"
        params.append(status)
    if item_type:
        where_clause += " AND item_type = %s"
        params.append(item_type)
    
    # 查询总数
    count_query = f"SELECT COUNT(*) as total FROM lost_items {where_clause}"
    cur.execute(count_query, params)
    total = cur.fetchone()['total']
    
    # 查询分页数据
    query = f"SELECT * FROM lost_items {where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([page_size, (page - 1) * page_size])
    
    cur.execute(query, params)
    items = cur.fetchall()
    cur.close()
    conn.close()
    
    return {
        "items": [serialize_row(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@app.post("/api/lost-items", response_model=LostItemResponse)
def create_lost_item(item: LostItemCreate, request: Request):
    current_user = get_current_user(request)
    verify_csrf_origin(request)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    vector = _build_vector(item.item_name, item.description, item.image_url)
    try:
        # 显式获取下一个 ID（序列权限变通方案）
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM lost_items")
        next_id = cur.fetchone()[0]

        cur.execute(
            """INSERT INTO lost_items
               (id, item_name, item_type, description, location, lost_time, status,
                image_url, contact_person, contact_phone, contact_qq, user_id, vector)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector) RETURNING *""",
            (next_id, item.item_name, none_if_empty(item.item_type),
             none_if_empty(item.description), none_if_empty(item.location),
             none_if_empty(item.lost_time), none_if_empty(item.status) or 'lost',
             none_if_empty(item.image_url), item.contact_person,
             none_if_empty(item.contact_phone), none_if_empty(item.contact_qq),
             current_user["id"],
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
        conn.close()

@app.get("/api/lost-items/{item_id}", response_model=LostItemResponse)
def get_lost_item(item_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM lost_items WHERE id = %s", (item_id,))
    item = cur.fetchone()
    cur.close()
    conn.close()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    return serialize_row(item)

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
        
        if item.item_name:
            update_fields.append("item_name = %s")
            params.append(item.item_name)
        if item.item_type:
            update_fields.append("item_type = %s")
            params.append(item.item_type)
        if item.description:
            update_fields.append("description = %s")
            params.append(item.description)
        if item.location:
            update_fields.append("location = %s")
            params.append(item.location)
        if item.found_time:
            update_fields.append("found_time = %s")
            params.append(item.found_time)
        if item.status:
            update_fields.append("status = %s")
            params.append(item.status)
        if item.image_url:
            update_fields.append("image_url = %s")
            params.append(item.image_url)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="没有要更新的字段")

        if item.item_name or item.description or item.image_url:
            cur.execute("SELECT item_name, description, image_url FROM lost_items WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if row:
                new_name = item.item_name or row["item_name"]
                new_desc = item.description or row["description"]
                new_img = item.image_url or row["image_url"]
                vector = _build_vector(new_name, new_desc, new_img)
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
        conn.close()

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
        conn.close()

@app.get("/api/search")
def search_lost_items(
    query: str = Query(..., min_length=1),
    item_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    search_query = "SELECT * FROM lost_items WHERE 1=1"
    params = []
    
    if item_type:
        search_query += " AND item_type = %s"
        params.append(item_type)
    if status:
        search_query += " AND status = %s"
        params.append(status)
    
    search_query += " AND (item_name ILIKE %s OR description ILIKE %s OR location ILIKE %s)"
    params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    
    search_query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    
    cur.execute(search_query, params)
    items = cur.fetchall()
    cur.close()
    conn.close()
    
    return {"results": [serialize_row(item) for item in items]}


@app.get("/api/semantic-search")
def semantic_search(
    query: str = Query(..., min_length=1),
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
        cur.execute(
            """SELECT *, 1 - (vector <=> %s::vector) AS similarity
               FROM lost_items
               WHERE vector IS NOT NULL
               ORDER BY vector <=> %s::vector
               LIMIT %s""",
            (vector_str, vector_str, limit)
        )
        items = cur.fetchall()
        return {"results": [serialize_row(item) for item in items]}
    finally:
        cur.close()
        conn.close()


@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM lost_items WHERE status = 'lost'")
    lost_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM lost_items WHERE status = 'found'")
    found_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM lost_items")
    total_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return {
        "total_items": total_count,
        "lost_count": lost_count,
        "found_count": found_count,
        "user_count": user_count
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
