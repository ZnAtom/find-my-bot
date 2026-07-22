from fastapi import FastAPI, HTTPException, Query, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
from time import monotonic
import httpx
import base64
import json
import mimetypes
import psycopg2
import psycopg2.extras
import os
import uuid
import aiofiles
import io
from functools import lru_cache
from urllib.parse import unquote, urlparse
from PIL import Image, ImageOps
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
from retrieval import (
    bm25_recall,
    build_search_text,
    filter_vector_recall,
    hybrid_match_score,
    rrf_fuse,
    rule_rerank,
)

app = FastAPI(title="校园失物招领 API", version="1.0.0")


import asyncio
import logging

CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]
CAMPUS_MAP_TILE_BASE_URL = os.environ.get("CAMPUS_MAP_TILE_BASE_URL", "https://map.shanghaitech.edu.cn")
CAMPUS_MAP_TILE_TIMEOUT = float(os.environ.get("CAMPUS_MAP_TILE_TIMEOUT", "6"))

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
SCHOOL_API_URL = os.environ.get("SCHOOL_API_URL", "https://genaiapi.shanghaitech.edu.cn/api/v1/start")
SCHOOL_API_KEY = os.environ.get("SCHOOL_API_KEY")
SCHOOL_VISION_MODEL = os.environ.get("SCHOOL_VISION_MODEL", os.environ.get("SCHOOL_MODEL", "qwen2.5-vl-instruct"))
VISION_MAX_IMAGES = int(os.environ.get("VISION_MAX_IMAGES", "10"))
VISION_TIMEOUT_SECONDS = float(os.environ.get("VISION_TIMEOUT_SECONDS", "180"))
VISION_CONNECT_TIMEOUT_SECONDS = float(os.environ.get("VISION_CONNECT_TIMEOUT_SECONDS", "10"))
VISION_WRITE_TIMEOUT_SECONDS = float(os.environ.get("VISION_WRITE_TIMEOUT_SECONDS", "30"))
VISION_POOL_TIMEOUT_SECONDS = float(os.environ.get("VISION_POOL_TIMEOUT_SECONDS", "10"))
VISION_IMAGE_MAX_BYTES = int(os.environ.get("VISION_IMAGE_MAX_BYTES", str(10 * 1024 * 1024)))
VISION_IMAGE_MAX_SIDE = int(os.environ.get("VISION_IMAGE_MAX_SIDE", "1600"))
VISION_IMAGE_JPEG_QUALITY = int(os.environ.get("VISION_IMAGE_JPEG_QUALITY", "85"))
RETRIEVAL_CANDIDATE_LIMIT = min(10, max(1, int(os.environ.get("RETRIEVAL_CANDIDATE_LIMIT", "10"))))
BM25_WEIGHT = max(0.0, float(os.environ.get("BM25_WEIGHT", "0.7")))
VECTOR_WEIGHT = max(0.0, float(os.environ.get("VECTOR_WEIGHT", "0.3")))
VECTOR_SIMILARITY_THRESHOLD = float(os.environ.get("VECTOR_SIMILARITY_THRESHOLD", "0.48"))
VECTOR_SIMILARITY_MAX_DROP = float(os.environ.get("VECTOR_SIMILARITY_MAX_DROP", "0.08"))
RESULT_RELEVANCE_THRESHOLD = float(os.environ.get("RESULT_RELEVANCE_THRESHOLD", "0.65"))
UPLOAD_RATE_LIMIT_COUNT = int(os.environ.get("UPLOAD_RATE_LIMIT_COUNT", "20"))
UPLOAD_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("UPLOAD_RATE_LIMIT_WINDOW_SECONDS", "3600"))
IMAGE_ANALYSIS_RATE_LIMIT_COUNT = int(os.environ.get("IMAGE_ANALYSIS_RATE_LIMIT_COUNT", "10"))
IMAGE_ANALYSIS_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("IMAGE_ANALYSIS_RATE_LIMIT_WINDOW_SECONDS", "3600"))

ITEM_TYPE_OPTIONS = {"证件卡片", "电子产品", "衣物鞋帽", "学习用品", "钱包钥匙", "其他"}

IMAGE_ANALYSIS_PROMPT = """你是“校园失物招领图片信息提取器”。

任务：
根据用户上传的图片，提取可直接用于发布失物招领记录的物品字段。
只关注物品本身，不提取地点、时间、联系人、手机号、QQ、学号、证件号等信息。
只输出严格 JSON，不要解释，不要 Markdown，不要多余文本。

规则：
1. 只根据图片中明确可见的信息填写，不要猜测。
2. 多张图一起分析，合并重复信息。
3. 物品名称要短而具体，优先包含颜色、品牌或类型，例如“黑色双肩包”“校园一卡通”“AirPods Pro 耳机”。
4. 物品分类只能从以下 6 类里选最接近的一项：证件卡片、电子产品、衣物鞋帽、学习用品、钱包钥匙、其他。
5. 描述要简短但完整，包含颜色、品牌、外观、数量、材质、特殊标记、包装或配件等可见特征。
6. 如果图片里出现姓名，只允许用“姓+同学”的形式描述，例如“卡面疑似有王同学姓名”；不要输出完整姓名。
7. 不要输出手机号、QQ、学号、证件号、身份证号、条形码/二维码内容、邮箱等敏感信息。
8. 不确定的字段返回空字符串；注意事项放入 notes。

输出格式：
{
  "item_name": "",
  "item_type": "",
  "description": "",
  "notes": []
}"""

# 挂载上传目录为静态文件服务
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

_rate_limit_buckets: dict[tuple[str, str], list[float]] = {}


def _client_rate_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(request: Request, bucket: str, max_requests: int, window_seconds: int):
    if max_requests <= 0 or window_seconds <= 0:
        return

    now = monotonic()
    key = (bucket, _client_rate_key(request))
    window_start = now - window_seconds
    requests = [timestamp for timestamp in _rate_limit_buckets.get(key, []) if timestamp > window_start]

    if len(requests) >= max_requests:
        raise HTTPException(status_code=429, detail="操作过于频繁，请稍后再试")

    requests.append(now)
    _rate_limit_buckets[key] = requests


@app.get("/api/campus-map/tiles/{zoom}/tile{x}_{y}.png")
async def proxy_campus_map_tile(zoom: int, x: int, y: int):
    if zoom < 17 or zoom > 19 or x < 0 or y < 0:
        raise HTTPException(status_code=404, detail="地图瓦片不存在")

    tile_url = f"{CAMPUS_MAP_TILE_BASE_URL}/tiles/{zoom}/tile{x}_{y}.png"
    try:
        async with httpx.AsyncClient(timeout=CAMPUS_MAP_TILE_TIMEOUT) as client:
            response = await client.get(
                tile_url,
                headers={
                    "Accept": "image/png,image/*;q=0.8,*/*;q=0.5",
                    "Referer": "https://map.shanghaitech.edu.cn/",
                    "User-Agent": "FoundIt campus map tile proxy",
                },
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="校园地图暂时无法访问")

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="地图瓦片不存在")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="校园地图暂时无法访问")

    return Response(
        content=response.content,
        media_type=response.headers.get("content-type", "image/png"),
        headers={
            "Cache-Control": "public, max-age=86400",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.post("/api/upload")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """上传图片，返回可访问的 URL"""
    verify_csrf_origin(request)
    _check_rate_limit(request, "upload", UPLOAD_RATE_LIMIT_COUNT, UPLOAD_RATE_LIMIT_WINDOW_SECONDS)

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
    user, is_new_user = get_or_create_user(userinfo)
    session_token = create_session_token(user["id"])

    # 新注册用户：插入欢迎通知
    if is_new_user:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO notifications
                   (user_id, title, message, notification_type)
                   VALUES (%s, %s, %s, %s)""",
                (
                    user["id"],
                    "👋 欢迎来到 FoundIt！",
                    "网站正在紧锣密鼓地打磨中，如果你发现 bug 或有任何建议，请毫不犹豫地告诉我们。联系管理员：jxy264@qq.com。你的每一条反馈，都是我们进步的动力 ❤️",
                    "system",
                ),
            )
            conn.commit()
            cur.close()
            release_db_connection(conn)
        except Exception:
            pass  # 通知写入失败不影响登录流程

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


class ImageAnalysisRequest(BaseModel):
    image_urls: List[str] = Field(default_factory=list)


class ImageAnalysisResponse(BaseModel):
    item_name: str = ""
    item_type: str = ""
    description: str = ""
    notes: List[str] = Field(default_factory=list)



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


def _normalize_uploaded_image_urls(image_url: Optional[str]) -> Optional[str]:
    if not image_url:
        return None

    normalized_urls = []
    for raw_url in image_url.split(","):
        value = raw_url.strip()
        if not value:
            continue

        parsed = urlparse(value)
        if parsed.scheme or parsed.netloc:
            raise HTTPException(status_code=400, detail="物品图片只能使用本站上传的图片")

        path = unquote(value)
        if not path.startswith("/uploads/"):
            raise HTTPException(status_code=400, detail="物品图片只能使用本站上传的图片")

        filename = path.removeprefix("/uploads/")
        if not filename or "/" in filename or "\\" in filename or filename in (".", ".."):
            raise HTTPException(status_code=400, detail="图片路径无效")

        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="图片类型无效")

        normalized_url = f"/uploads/{filename}"
        if not _image_url_to_path(normalized_url):
            raise HTTPException(status_code=400, detail="图片不存在或路径无效")

        normalized_urls.append(normalized_url)

    return ",".join(normalized_urls) if normalized_urls else None


def _iter_image_paths(image_url: Optional[str]) -> list[str]:
    if not image_url:
        return []
    paths = []
    for raw_url in image_url.split(","):
        path = _image_url_to_path(raw_url)
        if path:
            paths.append(path)
    return paths


def _image_to_data_url(path: str) -> str:
    resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
    target_sizes = [VISION_IMAGE_MAX_SIDE, 1280, 1024, 768]
    target_qualities = [VISION_IMAGE_JPEG_QUALITY, 75, 65]

    try:
        with Image.open(path) as source:
            normalized = ImageOps.exif_transpose(source)
            if normalized.mode != "RGB":
                # 统一转成 JPEG，减少 Base64 请求体体积，并避免方向元数据影响模型识别。
                if "A" in normalized.getbands():
                    background = Image.new("RGB", normalized.size, (255, 255, 255))
                    background.paste(normalized, mask=normalized.getchannel("A"))
                    normalized = background
                else:
                    normalized = normalized.convert("RGB")

            for max_side in target_sizes:
                candidate = normalized.copy()
                candidate.thumbnail((max_side, max_side), resample)

                for quality in target_qualities:
                    buffer = io.BytesIO()
                    candidate.save(buffer, format="JPEG", quality=quality, optimize=True)
                    encoded = buffer.getvalue()
                    if len(encoded) <= VISION_IMAGE_MAX_BYTES:
                        image_base64 = base64.b64encode(encoded).decode("utf-8")
                        return f"data:image/jpeg;base64,{image_base64}"
    except HTTPException:
        raise
    except Exception as exc:
        logging.warning("Prepare image for school analysis failed: %s", exc)
        raise HTTPException(status_code=400, detail="图片处理失败，请尝试重新上传更清晰的图片")

    raise HTTPException(status_code=400, detail="图片压缩后仍超过学校图像理解接口 10MB 限制")


def _is_remote_image_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _image_ref_to_school_url(image_ref: str) -> str:
    if _is_remote_image_url(image_ref):
        return image_ref.strip()
    return _image_to_data_url(image_ref)


def _school_vision_model_candidates() -> list[str]:
    configured = (SCHOOL_VISION_MODEL or "").strip()
    candidates = []
    for model_name in ("qwen2.5-vl-instruct", configured, "qwen-instruct"):
        if model_name and model_name not in candidates:
            candidates.append(model_name)
    return candidates


def _school_http_timeout() -> httpx.Timeout:
    return httpx.Timeout(
        connect=VISION_CONNECT_TIMEOUT_SECONDS,
        read=VISION_TIMEOUT_SECONDS,
        write=VISION_WRITE_TIMEOUT_SECONDS,
        pool=VISION_POOL_TIMEOUT_SECONDS,
    )


def _message_content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(part for part in parts if part)
    return str(content or "")


def _parse_json_object(text: str) -> dict:
    if not text:
        raise ValueError("empty response")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start == -1:
        raise ValueError("response does not contain a JSON object")

    decoder = json.JSONDecoder()
    parsed, _ = decoder.raw_decode(text[start:])
    if not isinstance(parsed, dict):
        raise ValueError("response JSON is not an object")
    return parsed


def _clean_analysis_result(data: dict) -> ImageAnalysisResponse:
    item_name = str(data.get("item_name") or "").strip()
    item_type = str(data.get("item_type") or "").strip()
    description = str(data.get("description") or "").strip()
    notes = data.get("notes") or []

    if item_type and item_type not in ITEM_TYPE_OPTIONS:
        item_type = "其他"

    if not isinstance(notes, list):
        notes = [str(notes)]

    return ImageAnalysisResponse(
        item_name=item_name[:80],
        item_type=item_type,
        description=description[:600],
        notes=[str(note).strip()[:120] for note in notes if str(note).strip()][:5],
    )


async def _call_school_image_analysis(image_refs: list[str]) -> ImageAnalysisResponse:
    if not SCHOOL_API_KEY:
        raise HTTPException(status_code=503, detail="图片识别服务未配置")

    content = [{"type": "text", "text": IMAGE_ANALYSIS_PROMPT}]
    for image_ref in image_refs:
        content.append({"type": "image_url", "image_url": {"url": _image_ref_to_school_url(image_ref)}})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SCHOOL_API_KEY}",
    }
    had_timeout = False

    for model_name in _school_vision_model_candidates():
        payload = {
            "stream": False,
            "model": model_name,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.1,
        }

        try:
            transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
            async with httpx.AsyncClient(timeout=_school_http_timeout(), transport=transport) as client:
                response = await client.post(SCHOOL_API_URL, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            had_timeout = True
            logging.warning(
                "School image analysis timed out with model=%s read_timeout=%ss: %s",
                model_name,
                VISION_TIMEOUT_SECONDS,
                exc,
            )
            continue
        except httpx.HTTPError as exc:
            logging.warning("School image analysis HTTP error with model=%s: %s", model_name, exc)
            continue

        if response.status_code != 200:
            logging.warning(
                "School image analysis failed with model=%s status=%s body=%s",
                model_name,
                response.status_code,
                response.text[:500],
            )
            continue

        try:
            data = response.json()
            message = data["choices"][0]["message"]
            content_text = _message_content_to_text(message.get("content"))
            parsed = _parse_json_object(content_text)
            return _clean_analysis_result(parsed)
        except Exception as exc:
            logging.warning("Image analysis parse failed with model=%s: %s", model_name, exc)
            continue

    if had_timeout:
        raise HTTPException(status_code=504, detail="图片识别服务响应超时，请稍后重试")
    raise HTTPException(status_code=502, detail="图片识别服务暂不可用")


@app.post("/api/image-analysis", response_model=ImageAnalysisResponse)
async def analyze_uploaded_images(payload: ImageAnalysisRequest, request: Request):
    verify_csrf_origin(request)
    _check_rate_limit(
        request,
        "image-analysis",
        IMAGE_ANALYSIS_RATE_LIMIT_COUNT,
        IMAGE_ANALYSIS_RATE_LIMIT_WINDOW_SECONDS,
    )

    image_urls = [url for url in payload.image_urls if url and url.strip()]
    if not image_urls:
        raise HTTPException(status_code=400, detail="请先上传图片")
    if len(image_urls) > VISION_MAX_IMAGES:
        raise HTTPException(status_code=400, detail=f"单次最多分析 {VISION_MAX_IMAGES} 张图片")

    image_refs = []
    for image_url in image_urls:
        image_url = image_url.strip()
        if _is_remote_image_url(image_url):
            image_refs.append(image_url)
            continue

        path = _image_url_to_path(image_url)
        if not path:
            raise HTTPException(status_code=400, detail="图片不存在或路径无效")
        image_refs.append(path)

    return await _call_school_image_analysis(image_refs)


@lru_cache(maxsize=128)
def _build_vector(item_name: str, location: Optional[str] = None, lost_time: Optional[str] = None, description: Optional[str] = None, image_url: Optional[str] = None) -> Optional[str]:
    try:
        image_paths = _iter_image_paths(image_url)
        # Search vectors intentionally exclude location/time so they describe only the item.
        vec = encode_multimodal(item_name, "", "", description or "", image_paths)
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
    item.pop("vector", None)
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


class AdminNotificationRequest(BaseModel):
    title: str
    message: Optional[str] = None
    user_ids: Optional[List[int]] = None  # None = all users


@app.post("/api/admin/notifications")
def admin_send_notification(body: AdminNotificationRequest, request: Request):
    """管理员向所有用户或指定用户发送系统通知"""
    require_admin(request)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if body.user_ids and len(body.user_ids) > 0:
            # 发送给指定用户
            for uid in body.user_ids:
                cur.execute(
                    """INSERT INTO notifications (user_id, title, message, notification_type)
                       VALUES (%s, %s, %s, 'system')""",
                    (uid, body.title, body.message),
                )
        else:
            # 发送给所有用户
            cur.execute(
                """INSERT INTO notifications (user_id, title, message, notification_type)
                   SELECT id, %s, %s, 'system' FROM users""",
                (body.title, body.message),
            )
        conn.commit()
        count = cur.rowcount if not body.user_ids else len(body.user_ids)
        return {"success": True, "sent_count": count}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"发送通知失败: {e}")
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
    page_size: int = 20,
    all_items: bool = Query(False, alias="all"),
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
    
    query = f"SELECT * FROM lost_items {where_clause} ORDER BY created_at DESC"
    if not all_items:
        query += " LIMIT %s OFFSET %s"
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
        "page": 1 if all_items else page,
        "page_size": total if all_items else page_size,
    }

class MatchCheckRequest(LostItemCreate):
    pass

@app.post("/api/match-check")
def match_check(item: MatchCheckRequest, request: Request, limit: int = Query(10, ge=1)):
    direction, _ = _resolve_create_state(item.direction, item.status, item.post_type)
    vector = _build_vector(item.item_name, item.location, str(item.lost_time) if item.lost_time else "", item.description, item.image_url)
    target_direction = "found" if direction == "lost" else "lost"
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        lexical_params = [target_direction, "active"]
        cur.execute(
            """SELECT * FROM lost_items
               WHERE direction = %s AND status = %s""",
            lexical_params,
        )
        lexical_items = cur.fetchall()

        vector_items = []
        if vector:
            cur.execute(
                """SELECT *, 1 - (vector <=> %s::vector) AS similarity
                   FROM lost_items
                   WHERE vector IS NOT NULL
                     AND direction = %s
                     AND status = 'active'
                   ORDER BY vector <=> %s::vector
                   LIMIT %s""",
                (vector, target_direction, vector, RETRIEVAL_CANDIDATE_LIMIT),
            )
            vector_items = filter_vector_recall(
                cur.fetchall(),
                minimum_similarity=VECTOR_SIMILARITY_THRESHOLD,
                maximum_drop=VECTOR_SIMILARITY_MAX_DROP,
            )

        bm25_items = bm25_recall(build_search_text(item), lexical_items, RETRIEVAL_CANDIDATE_LIMIT)
        fused = rrf_fuse(
            vector_items,
            bm25_items,
            min(limit, RETRIEVAL_CANDIDATE_LIMIT),
            vector_weight=VECTOR_WEIGHT,
            bm25_weight=BM25_WEIGHT,
        )
        items = rule_rerank(fused, item)
        current_user = get_optional_user(request)
        claim_item_ids = _get_claim_item_ids_for_user(cur, current_user)
        results = []
        for row, retrieval_score in items[:limit]:
            display_score = hybrid_match_score(item.item_name, row)
            if display_score < RESULT_RELEVANCE_THRESHOLD:
                continue
            serialized = serialize_item_for_user(row, current_user, claim_item_ids)
            serialized["vector_similarity"] = serialized.get("similarity")
            serialized["similarity"] = round(display_score, 4)
            serialized["retrieval_score"] = round(retrieval_score, 6)
            results.append(serialized)
        return {"results": results}
    finally:
        cur.close()
        release_db_connection(conn)

@app.post("/api/lost-items", response_model=LostItemResponse)
def create_lost_item(item: LostItemCreate, request: Request):
    verify_csrf_origin(request)
    direction, status = _resolve_create_state(item.direction, item.status, item.post_type)
    image_url = _normalize_uploaded_image_urls(item.image_url)
    current_user = get_optional_user(request)
    has_contact = any(none_if_empty(value) for value in (item.contact_phone, item.contact_qq, item.contact_email))
    if direction == "lost" and not current_user:
        raise HTTPException(status_code=401, detail="发布寻物信息需要先登录")
    if direction == "lost" and not has_contact:
        raise HTTPException(status_code=400, detail="发布寻物信息至少需要填写一种联系方式")
    if direction == "found" and not current_user and has_contact:
        raise HTTPException(status_code=401, detail="匿名招领不能填写联系方式，请登录后实名发布")

    storage_location = none_if_empty(item.storage_location.strip() if isinstance(item.storage_location, str) else item.storage_location)
    if direction == "found" and not storage_location:
        raise HTTPException(status_code=400, detail="发布招领信息需要填写现在存放处")

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
    vector = _build_vector(item.item_name, item.location, str(item.lost_time) if item.lost_time else "", item.description, image_url)
    try:
        cur.execute(
            """INSERT INTO lost_items
               (item_name, item_type, description, location, storage_location, lost_time, direction, status, contact_visibility,
                image_url, contact_person, contact_phone, contact_qq, contact_email, user_id, vector)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector) RETURNING *""",
            (item.item_name, none_if_empty(item.item_type),
             none_if_empty(item.description), none_if_empty(item.location),
             storage_location, none_if_empty(item.lost_time), direction, status, contact_visibility,
             image_url, contact_person,
             none_if_empty(item.contact_phone), none_if_empty(item.contact_qq), none_if_empty(item.contact_email),
             current_user["id"] if current_user else None,
             none_if_empty(vector))
        )
        conn.commit()
        new_item = cur.fetchone()
        return serialize_row(new_item)
    except Exception:
        conn.rollback()
        logging.exception("Create lost item failed")
        raise HTTPException(status_code=400, detail="创建失物信息失败")
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
            image_url = _normalize_uploaded_image_urls(item.image_url)
            update_fields.append("image_url = %s")
            params.append(image_url)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="没有要更新的字段")

        if item.item_name or item.description or item.location or item.found_time or item.image_url is not None:
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
                new_img = _normalize_uploaded_image_urls(item.image_url) if item.image_url is not None else row["image_url"]
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
    
    search_query += " AND (item_name ILIKE %s OR description ILIKE %s)"
    params.extend([f"%{query}%", f"%{query}%"])
    
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
    limit: int = Query(10, ge=1),
):
    try:
        vec = encode_text(query)
    except Exception:
        raise HTTPException(status_code=500, detail="向量模型未就绪")

    vector_str = _vector_str(vec)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        lexical_where = "WHERE 1=1"
        lexical_params = []
        lexical_where = _append_item_filters(
            lexical_where,
            lexical_params,
            status=status,
            direction=direction,
            post_type=post_type,
            item_type=item_type,
        )
        cur.execute(
            f"SELECT * FROM lost_items {lexical_where}",
            lexical_params,
        )
        lexical_items = cur.fetchall()

        vector_where = "WHERE vector IS NOT NULL"
        vector_params = [vector_str]
        vector_where = _append_item_filters(
            vector_where,
            vector_params,
            status=status,
            direction=direction,
            post_type=post_type,
            item_type=item_type,
        )
        vector_params.extend([vector_str, RETRIEVAL_CANDIDATE_LIMIT])
        cur.execute(
            f"""SELECT *, 1 - (vector <=> %s::vector) AS similarity
                FROM lost_items
                {vector_where}
                ORDER BY vector <=> %s::vector
                LIMIT %s""",
            vector_params,
        )
        vector_items = filter_vector_recall(
            cur.fetchall(),
            minimum_similarity=VECTOR_SIMILARITY_THRESHOLD,
            maximum_drop=VECTOR_SIMILARITY_MAX_DROP,
        )
        bm25_items = bm25_recall(query, lexical_items, RETRIEVAL_CANDIDATE_LIMIT)
        items = rrf_fuse(
            vector_items,
            bm25_items,
            min(limit, RETRIEVAL_CANDIDATE_LIMIT),
            vector_weight=VECTOR_WEIGHT,
            bm25_weight=BM25_WEIGHT,
        )
        current_user = get_optional_user(request)
        claim_item_ids = _get_claim_item_ids_for_user(cur, current_user)
        results = []
        for item, retrieval_score in items:
            display_score = hybrid_match_score(query, item)
            if display_score < RESULT_RELEVANCE_THRESHOLD:
                continue
            serialized = serialize_item_for_user(item, current_user, claim_item_ids)
            serialized["vector_similarity"] = serialized.get("similarity")
            serialized["similarity"] = round(display_score, 4)
            serialized["retrieval_score"] = round(retrieval_score, 6)
            results.append(serialized)
        return {"results": results}
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
