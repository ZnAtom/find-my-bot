from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import uuid
from pathlib import Path
from typing import Any, Optional

import httpx
import psycopg2
import psycopg2.extras

from config_env import PROJECT_ROOT, load_project_env, resolve_project_path
from embedding import encode_text, embedding_enabled
from retrieval import bm25_recall, filter_vector_recall, hybrid_match_score, rrf_fuse, tokenize

load_project_env()

DEFAULT_SUPPORT_DOCS_DIR = PROJECT_ROOT / "doc" / "support"
_configured_support_docs_dir = Path(
    os.environ.get("SUPPORT_DOCS_DIR") or DEFAULT_SUPPORT_DOCS_DIR
).expanduser()
if not _configured_support_docs_dir.is_absolute():
    _configured_support_docs_dir = resolve_project_path(_configured_support_docs_dir)
SUPPORT_DOCS_DIR = _configured_support_docs_dir

SCHOOL_API_URL = os.environ.get("SCHOOL_API_URL", "https://genaiapi.shanghaitech.edu.cn/api/v1/start")
SCHOOL_API_KEY = os.environ.get("SCHOOL_API_KEY")
SUPPORT_LLM_MODEL = os.environ.get(
    "SUPPORT_LLM_MODEL",
    os.environ.get("SCHOOL_MODEL", os.environ.get("SCHOOL_VISION_MODEL", "GPT-5.5")),
)
SUPPORT_LLM_TIMEOUT_SECONDS = float(os.environ.get("SUPPORT_LLM_TIMEOUT_SECONDS", "60"))
SUPPORT_KNOWLEDGE_LIMIT = max(1, int(os.environ.get("SUPPORT_KNOWLEDGE_LIMIT", "6")))
SUPPORT_ITEM_LIMIT = max(1, int(os.environ.get("SUPPORT_ITEM_LIMIT", "5")))
SUPPORT_MAX_CONTEXT_CHARS = max(1000, int(os.environ.get("SUPPORT_MAX_CONTEXT_CHARS", "8000")))
VECTOR_DIM = int(os.environ.get("VECTOR_DIM", "1536"))
RETRIEVAL_CANDIDATE_LIMIT = min(10, max(1, int(os.environ.get("RETRIEVAL_CANDIDATE_LIMIT", "10"))))
BM25_WEIGHT = max(0.0, float(os.environ.get("BM25_WEIGHT", "0.7")))
VECTOR_WEIGHT = max(0.0, float(os.environ.get("VECTOR_WEIGHT", "0.3")))
VECTOR_SIMILARITY_THRESHOLD = float(os.environ.get("VECTOR_SIMILARITY_THRESHOLD", "0.48"))
VECTOR_SIMILARITY_MAX_DROP = float(os.environ.get("VECTOR_SIMILARITY_MAX_DROP", "0.08"))
RESULT_RELEVANCE_THRESHOLD = float(os.environ.get("RESULT_RELEVANCE_THRESHOLD", "0.65"))

_schema_ready = False
_embedding_unavailable = False


SUPPORT_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS support_knowledge_sources (
    id SERIAL PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_knowledge_chunks (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES support_knowledge_sources(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    embedding JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS support_chat_sessions (
    id UUID PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    anonymous_key TEXT,
    channel VARCHAR(20) NOT NULL DEFAULT 'web',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_chat_messages (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES support_chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    sources JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT support_chat_messages_role_check CHECK (role IN ('user', 'assistant'))
);

CREATE INDEX IF NOT EXISTS idx_support_knowledge_chunks_source_id
    ON support_knowledge_chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_support_chat_sessions_user_id
    ON support_chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_support_chat_sessions_anonymous_key
    ON support_chat_sessions(anonymous_key);
CREATE INDEX IF NOT EXISTS idx_support_chat_messages_session_id
    ON support_chat_messages(session_id);
"""


def ensure_support_schema(conn) -> None:
    global _schema_ready
    if _schema_ready:
        return

    cur = conn.cursor()
    try:
        cur.execute(SUPPORT_SCHEMA_SQL)
        conn.commit()
        _schema_ready = True
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def serialize_row(row: Any) -> dict[str, Any]:
    result = dict(row)
    for key, value in result.items():
        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
    return result


def make_anonymous_key(raw_key: str) -> str:
    secret = os.environ.get("JWT_SECRET", "foundit-support")
    digest = hashlib.sha256(f"{secret}:support:{raw_key}".encode("utf-8")).hexdigest()
    return digest[:40]


def extract_markdown_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return fallback


def _split_long_text(text: str, max_chars: int) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        paragraph_len = len(paragraph)
        if current and current_len + paragraph_len + 2 > max_chars:
            chunks.append("\n\n".join(current).strip())
            current = []
            current_len = 0
        if paragraph_len > max_chars:
            chunks.append(paragraph[:max_chars].strip())
            remainder = paragraph[max_chars:].strip()
            if remainder:
                current = [remainder]
                current_len = len(remainder)
            continue
        current.append(paragraph)
        current_len += paragraph_len + 2

    if current:
        chunks.append("\n\n".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def chunk_markdown(text: str, source_title: str, max_chars: int = 1200) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    heading = source_title
    buffer: list[str] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        buffer.clear()
        if not body:
            return
        for part in _split_long_text(body, max_chars):
            chunks.append({"title": heading, "content": part})

    for line in text.splitlines():
        heading_match = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if heading_match:
            flush()
            heading = heading_match.group(2).strip()
            continue
        if line.startswith("# "):
            continue
        buffer.append(line)

    flush()
    return chunks or [{"title": source_title, "content": text.strip()}]


def _docs_relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _try_encode_text(text: str) -> Optional[list[float]]:
    global _embedding_unavailable
    if _embedding_unavailable or not embedding_enabled():
        return None
    try:
        return encode_text(text)
    except Exception:
        _embedding_unavailable = True
        logging.exception("Support embedding unavailable; support RAG falls back to BM25")
        return None


def _source_needs_embedding_refresh(cur, source_id: int) -> bool:
    if not embedding_enabled():
        return False
    cur.execute(
        """SELECT COUNT(*) AS total,
                  COUNT(*) FILTER (WHERE embedding IS NULL) AS missing
           FROM support_knowledge_chunks
           WHERE source_id = %s""",
        (source_id,),
    )
    row = cur.fetchone()
    if not row:
        return True
    return int(row["total"] or 0) == 0 or int(row["missing"] or 0) > 0


def import_support_knowledge(conn, docs_dir: Optional[Path] = None, *, force: bool = False) -> dict[str, int | str]:
    ensure_support_schema(conn)
    root = Path(docs_dir or SUPPORT_DOCS_DIR).expanduser()
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    markdown_files = sorted(root.rglob("*.md")) if root.exists() else []
    stats: dict[str, int | str] = {
        "sources": 0,
        "chunks": 0,
        "skipped": 0,
        "refreshed": 0,
        "embedding": "enabled" if embedding_enabled() else "disabled",
    }

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        for path in markdown_files:
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue

            rel_path = _docs_relative_path(path)
            source_title = extract_markdown_title(text, path.stem)
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            cur.execute(
                "SELECT id, content_hash FROM support_knowledge_sources WHERE path = %s",
                (rel_path,),
            )
            existing = cur.fetchone()
            if existing and existing["content_hash"] == content_hash and not force:
                if not _source_needs_embedding_refresh(cur, existing["id"]):
                    stats["skipped"] = int(stats["skipped"]) + 1
                    continue
                stats["refreshed"] = int(stats["refreshed"]) + 1

            cur.execute(
                """INSERT INTO support_knowledge_sources (path, title, content_hash, updated_at)
                   VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                   ON CONFLICT (path)
                   DO UPDATE SET title = EXCLUDED.title,
                                 content_hash = EXCLUDED.content_hash,
                                 updated_at = CURRENT_TIMESTAMP
                   RETURNING id""",
                (rel_path, source_title, content_hash),
            )
            source_id = cur.fetchone()["id"]
            cur.execute("DELETE FROM support_knowledge_chunks WHERE source_id = %s", (source_id,))

            for index, chunk in enumerate(chunk_markdown(text, source_title)):
                content = chunk["content"]
                embedding = _try_encode_text(f"{source_title}\n{chunk['title']}\n{content}")
                cur.execute(
                    """INSERT INTO support_knowledge_chunks
                       (source_id, chunk_index, title, content, token_count, embedding)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        source_id,
                        index,
                        chunk["title"],
                        content,
                        len(tokenize(content)),
                        psycopg2.extras.Json(embedding) if embedding is not None else None,
                    ),
                )
                stats["chunks"] = int(stats["chunks"]) + 1

            stats["sources"] = int(stats["sources"]) + 1

        conn.commit()
        return stats
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _decode_embedding(value: Any) -> Optional[list[float]]:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    if not isinstance(value, list):
        return None
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    size = min(len(left), len(right))
    if size <= 0:
        return 0.0
    left = left[:size]
    right = right[:size]
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _load_knowledge_chunks(conn) -> list[dict[str, Any]]:
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(
            """SELECT c.id, c.source_id, c.chunk_index, c.title, c.content, c.embedding,
                      s.path, s.title AS source_title
               FROM support_knowledge_chunks c
               JOIN support_knowledge_sources s ON s.id = c.source_id
               ORDER BY s.path, c.chunk_index"""
        )
        return [serialize_row(row) for row in cur.fetchall()]
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        return []
    finally:
        cur.close()


def retrieve_knowledge(conn, query: str, limit: int = SUPPORT_KNOWLEDGE_LIMIT) -> list[dict[str, Any]]:
    rows = _load_knowledge_chunks(conn)
    if not rows:
        return []

    search_rows = [
        {
            "id": row["id"],
            "item_name": row["title"],
            "item_type": row["source_title"],
            "description": row["content"],
            "_row": row,
        }
        for row in rows
    ]
    bm25_rows = bm25_recall(query, search_rows, limit)
    scores: dict[int, float] = {}
    by_id: dict[int, dict[str, Any]] = {row["id"]: row["_row"] for row in search_rows}

    for rank, row in enumerate(bm25_rows, start=1):
        scores[row["id"]] = scores.get(row["id"], 0.0) + 0.7 / (60 + rank)

    query_embedding = _try_encode_text(query)
    if query_embedding is not None:
        vector_hits = []
        for row in rows:
            embedding = _decode_embedding(row.get("embedding"))
            if not embedding:
                continue
            similarity = _cosine_similarity(query_embedding, embedding)
            vector_hits.append((row, similarity))
        vector_hits.sort(key=lambda item: item[1], reverse=True)
        for rank, (row, similarity) in enumerate(vector_hits[:limit], start=1):
            if similarity <= 0:
                continue
            scores[row["id"]] = scores.get(row["id"], 0.0) + 0.3 / (60 + rank)
            row["similarity"] = round(similarity, 4)

    if not scores:
        return []

    ranked_ids = sorted(scores, key=lambda row_id: scores[row_id], reverse=True)
    results = []
    for row_id in ranked_ids[:limit]:
        row = dict(by_id[row_id])
        row["retrieval_score"] = round(scores[row_id], 6)
        results.append(row)
    return results


_PERSONAL_QUERY_TERMS = (
    "我的发布",
    "我发布",
    "我的物品",
    "我的申请",
    "我申请",
    "我的认领",
    "我认领",
    "我捡到的",
    "我丢失的",
    "我的寻物",
    "我的招领",
    "我有哪些发布",
    "我发过",
    "我提交的",
)
_ITEM_SEARCH_TERMS = (
    "找",
    "搜索",
    "有没有",
    "丢",
    "丢了",
    "捡",
    "捡到",
    "招领",
    "寻物",
    "失物",
    "认领",
    "校园卡",
    "一卡通",
    "学生卡",
    "学生证",
    "耳机",
    "钥匙",
    "钱包",
    "水杯",
    "雨伞",
    "手机",
    "电脑",
    "书包",
    "证件",
)


def detect_intent(message: str, user: Optional[dict]) -> str:
    compact = re.sub(r"\s+", "", message)
    if user and any(term in compact for term in _PERSONAL_QUERY_TERMS):
        return "personal_data"
    if any(term in compact for term in _ITEM_SEARCH_TERMS):
        return "item_search"
    return "platform_help"


def _format_direction(value: Optional[str]) -> str:
    if value == "found":
        return "招领"
    if value == "lost":
        return "寻物"
    return "未知方向"


def _format_status(value: str) -> str:
    return {
        "active": "进行中",
        "recovered": "已找回",
        "expired": "已过期",
        "submitted": "已提交",
        "completed": "已完成",
        "rejected": "已拒绝",
    }.get(value, value or "未知")


def _shorten(value: Any, limit: int = 140) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _vector_str(values: list[float]) -> str:
    trimmed = values[:VECTOR_DIM]
    return "[" + ",".join(str(value) for value in trimmed) + "]"


def _lost_items_vector_column_exists(cur) -> bool:
    cur.execute(
        """SELECT EXISTS (
               SELECT 1
               FROM information_schema.columns
               WHERE table_name = 'lost_items'
                 AND column_name = 'vector'
           )"""
    )
    return bool(cur.fetchone()[0])


def search_public_items(conn, query: str, limit: int = SUPPORT_ITEM_LIMIT) -> list[dict[str, Any]]:
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        vector_str = None
        if _lost_items_vector_column_exists(cur) and embedding_enabled() and VECTOR_WEIGHT > 0:
            query_embedding = _try_encode_text(query)
            if query_embedding is not None:
                vector_str = _vector_str(query_embedding)

        cur.execute(
            """SELECT id, item_name, item_type, direction, status, description,
                      location, image_url, created_at, updated_at
               FROM lost_items
               WHERE status = 'active'
               ORDER BY updated_at DESC, created_at DESC
               LIMIT 400"""
        )
        rows = [serialize_row(row) for row in cur.fetchall()]

        vector_items = []
        if vector_str:
            cur.execute(
                """SELECT id, item_name, item_type, direction, status, description,
                          location, image_url, created_at, updated_at,
                          1 - (vector <=> %s::vector) AS similarity
                   FROM lost_items
                   WHERE status = 'active'
                     AND vector IS NOT NULL
                   ORDER BY vector <=> %s::vector
                   LIMIT %s""",
                (vector_str, vector_str, RETRIEVAL_CANDIDATE_LIMIT),
            )
            vector_items = filter_vector_recall(
                [serialize_row(row) for row in cur.fetchall()],
                minimum_similarity=VECTOR_SIMILARITY_THRESHOLD,
                maximum_drop=VECTOR_SIMILARITY_MAX_DROP,
            )
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        return []
    except Exception:
        conn.rollback()
        logging.exception("Support item search failed")
        return []
    finally:
        cur.close()

    bm25_items = bm25_recall(query, rows, RETRIEVAL_CANDIDATE_LIMIT)
    hits = rrf_fuse(
        vector_items,
        bm25_items,
        min(limit, RETRIEVAL_CANDIDATE_LIMIT),
        vector_weight=VECTOR_WEIGHT if vector_str else 0,
        bm25_weight=BM25_WEIGHT,
    )

    results = []
    for row, retrieval_score in hits:
        score = hybrid_match_score(query, row)
        if score < RESULT_RELEVANCE_THRESHOLD:
            continue
        results.append(
            {
                "id": row["id"],
                "item_name": row["item_name"],
                "item_type": row.get("item_type"),
                "direction": row.get("direction"),
                "status": row.get("status"),
                "description": _shorten(row.get("description"), 160),
                "location": _shorten(row.get("location"), 60),
                "image_url": row.get("image_url"),
                "created_at": row.get("created_at"),
                "score": round(score, 4),
                "vector_similarity": row.get("similarity"),
                "retrieval_score": round(retrieval_score, 6),
                "url": f"/#/lost/{row['id']}",
            }
        )
    return results


def load_personal_context(conn, user: Optional[dict]) -> Optional[dict[str, Any]]:
    if not user:
        return None

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(
            """SELECT id, item_name, item_type, direction, status, description,
                      location, created_at, updated_at
               FROM lost_items
               WHERE user_id = %s
               ORDER BY updated_at DESC, created_at DESC
               LIMIT 8""",
            (user["id"],),
        )
        items = [serialize_row(row) for row in cur.fetchall()]

        cur.execute(
            """SELECT cr.id, cr.item_id, cr.request_type, cr.status, cr.message, cr.created_at,
                      li.item_name, li.direction AS item_direction
               FROM claim_requests cr
               JOIN lost_items li ON li.id = cr.item_id
               WHERE cr.requester_user_id = %s OR cr.owner_user_id = %s
               ORDER BY cr.created_at DESC
               LIMIT 8""",
            (user["id"], user["id"]),
        )
        claims = [serialize_row(row) for row in cur.fetchall()]
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        return {"items": [], "claims": []}
    finally:
        cur.close()

    return {
        "items": [
            {
                "id": row["id"],
                "item_name": row["item_name"],
                "direction": row.get("direction"),
                "status": row.get("status"),
                "description": _shorten(row.get("description"), 120),
                "location": _shorten(row.get("location"), 60),
                "url": f"/#/lost/{row['id']}",
            }
            for row in items
        ],
        "claims": [
            {
                "id": row["id"],
                "item_id": row["item_id"],
                "item_name": row.get("item_name"),
                "request_type": row.get("request_type"),
                "status": row.get("status"),
                "message": _shorten(row.get("message"), 120),
                "created_at": row.get("created_at"),
                "url": f"/#/lost/{row['item_id']}",
            }
            for row in claims
        ],
    }


def _knowledge_context(chunks: list[dict[str, Any]]) -> str:
    lines = []
    for index, chunk in enumerate(chunks, start=1):
        lines.append(
            f"[K{index}] {chunk['source_title']} / {chunk['title']} ({chunk['path']})\n"
            f"{_shorten(chunk['content'], 900)}"
        )
    return "\n\n".join(lines)


def _item_context(items: list[dict[str, Any]]) -> str:
    lines = []
    for index, item in enumerate(items, start=1):
        parts = [
            f"[I{index}] #{item['id']} {item['item_name']}",
            f"类型:{item.get('item_type') or '未分类'}",
            f"方向:{_format_direction(item.get('direction'))}",
            f"状态:{_format_status(item.get('status'))}",
        ]
        if item.get("location"):
            parts.append(f"地点:{item['location']}")
        if item.get("description"):
            parts.append(f"描述:{item['description']}")
        parts.append(f"详情:{item['url']}")
        lines.append("；".join(parts))
    return "\n".join(lines)


def _personal_context(personal: Optional[dict[str, Any]]) -> str:
    if personal is None:
        return ""
    lines = ["我的发布："]
    if personal["items"]:
        for item in personal["items"]:
            lines.append(
                f"- #{item['id']} {item['item_name']}，{_format_direction(item.get('direction'))}，"
                f"{_format_status(item.get('status'))}，详情 {item['url']}"
            )
    else:
        lines.append("- 暂无发布记录")

    lines.append("我的申请：")
    if personal["claims"]:
        for claim in personal["claims"]:
            lines.append(
                f"- 申请 #{claim['id']}，物品 #{claim['item_id']} {claim.get('item_name') or ''}，"
                f"状态 {_format_status(claim.get('status'))}，详情 {claim['url']}"
            )
    else:
        lines.append("- 暂无申请记录")
    return "\n".join(lines)


def build_sources(
    knowledge_chunks: list[dict[str, Any]],
    item_results: list[dict[str, Any]],
    personal: Optional[dict[str, Any]],
    *,
    intent: str = "general",
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    if intent != "item_search":
        return sources

    for item in item_results:
        key = ("item", str(item["id"]))
        if key in seen:
            continue
        seen.add(key)
        parts = [
            _format_direction(item.get("direction")),
            _format_status(item.get("status")),
            item.get("item_type") or "未分类",
        ]
        if item.get("location"):
            parts.append(f"地点：{item['location']}")
        sources.append(
            {
                "type": "item",
                "title": f"#{item['id']} {item['item_name']}",
                "path": item["url"],
                "snippet": " · ".join(parts),
            }
        )

    return sources


def _build_messages(
    message: str,
    intent: str,
    knowledge_chunks: list[dict[str, Any]],
    item_results: list[dict[str, Any]],
    personal: Optional[dict[str, Any]],
    user: Optional[dict],
) -> list[dict[str, str]]:
    context_parts = []
    knowledge = _knowledge_context(knowledge_chunks)
    if knowledge:
        context_parts.append(f"【知识库】\n{knowledge}")
    items = _item_context(item_results)
    if items:
        context_parts.append(f"【物品搜索结果】\n{items}")
    personal_text = _personal_context(personal)
    if personal_text:
        context_parts.append(f"【个人数据】\n{personal_text}")

    context = "\n\n".join(context_parts)
    if len(context) > SUPPORT_MAX_CONTEXT_CHARS:
        context = context[:SUPPORT_MAX_CONTEXT_CHARS].rstrip()

    login_state = "已登录" if user else "未登录"
    system_prompt = (
        "你是 FoundIt 校园失物招领平台的第一阶段智能客服。"
        "只能回答平台使用、失物招领流程、物品搜索和登录用户个人记录相关问题。"
        "优先依据提供的知识库、物品搜索结果和个人数据回答；资料不足时明确说明无法确认。"
        "如果【物品搜索结果】非空，必须先列出最相关的候选物品，包含物品名称、招领/寻物方向、地点和详情入口；"
        "不要说没有线索或信息太少，只能说明这些是相似线索、不能确认归属。"
        "严禁输出手机号、QQ、邮箱、学号、证件号、二维码内容、条形码内容或完整姓名等敏感信息。"
        "涉及联系他人时，只能引导用户登录后进入物品详情页按平台流程申请联系或认领。"
        "回答要简短但完整，必要时用 2 到 4 个要点。"
    )
    user_prompt = (
        f"用户登录状态：{login_state}\n"
        f"识别到的意图：{intent}\n\n"
        f"{context or '【上下文】暂无可用资料'}\n\n"
        f"用户问题：{message}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _extract_llm_response_text(data: Any) -> Optional[str]:
    if not isinstance(data, dict):
        return None

    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
            if isinstance(content, list):
                pieces = []
                for part in content:
                    if isinstance(part, dict):
                        text = part.get("text") or part.get("content")
                        if text:
                            pieces.append(str(text))
                    elif isinstance(part, str):
                        pieces.append(part)
                if pieces:
                    return "\n".join(pieces).strip()

    data_obj = data.get("data")
    if isinstance(data_obj, dict):
        for key in ("content", "text", "output_text"):
            value = data_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        output = data_obj.get("output")
        if isinstance(output, dict):
            for key in ("content", "text", "answer"):
                value = output.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

    for key in ("content", "text", "output_text"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


async def call_support_llm(messages: list[dict[str, str]]) -> str:
    if not SCHOOL_API_KEY:
        raise RuntimeError("缺少 SCHOOL_API_KEY 环境变量，无法调用学校 GenAI API")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SCHOOL_API_KEY}",
    }
    payload = {
        "stream": False,
        "model": SUPPORT_LLM_MODEL,
        "messages": messages,
    }
    try:
        async with httpx.AsyncClient(timeout=SUPPORT_LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(SCHOOL_API_URL, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"学校 GenAI API 请求失败: {exc}") from exc
    if response.status_code >= 400:
        raise RuntimeError(f"学校 GenAI API 调用失败: {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError("学校 GenAI API 响应不是 JSON") from exc
    text = _extract_llm_response_text(data)
    if not text:
        raise RuntimeError("学校 GenAI API 响应格式异常")
    return text


def _get_or_create_session(
    cur,
    *,
    session_id: Optional[str],
    user: Optional[dict],
    anonymous_key: str,
    channel: str,
) -> str:
    requested_id = None
    if session_id:
        try:
            requested_id = str(uuid.UUID(str(session_id)))
        except ValueError:
            requested_id = None

    user_id = user["id"] if user else None
    if requested_id:
        cur.execute(
            """SELECT id, user_id, anonymous_key
               FROM support_chat_sessions
               WHERE id = %s""",
            (requested_id,),
        )
        existing = cur.fetchone()
        if existing:
            owns_session = (
                (user_id is not None and existing["user_id"] == user_id)
                or (user_id is None and existing["anonymous_key"] == anonymous_key)
            )
            if owns_session:
                cur.execute(
                    "UPDATE support_chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (requested_id,),
                )
                return requested_id

    new_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO support_chat_sessions (id, user_id, anonymous_key, channel)
           VALUES (%s, %s, %s, %s)""",
        (new_id, user_id, anonymous_key if user_id is None else None, channel),
    )
    return new_id


async def answer_support_chat(
    conn,
    *,
    message: str,
    user: Optional[dict],
    anonymous_key: str,
    session_id: Optional[str] = None,
    channel: str = "web",
) -> dict[str, Any]:
    clean_message = message.strip()
    if not clean_message:
        raise ValueError("message is required")

    ensure_support_schema(conn)
    intent = detect_intent(clean_message, user)
    knowledge_chunks = retrieve_knowledge(conn, clean_message, SUPPORT_KNOWLEDGE_LIMIT)
    item_results = search_public_items(conn, clean_message, SUPPORT_ITEM_LIMIT) if intent == "item_search" else []
    personal = load_personal_context(conn, user) if intent == "personal_data" else None

    messages = _build_messages(clean_message, intent, knowledge_chunks, item_results, personal, user)
    sources = build_sources(knowledge_chunks, item_results, personal, intent=intent)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        real_session_id = _get_or_create_session(
            cur,
            session_id=session_id,
            user=user,
            anonymous_key=anonymous_key,
            channel=channel,
        )
        cur.execute(
            """INSERT INTO support_chat_messages (session_id, role, content)
               VALUES (%s, 'user', %s)""",
            (real_session_id, clean_message),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

    answer = await call_support_llm(messages)

    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO support_chat_messages (session_id, role, content, sources)
               VALUES (%s, 'assistant', %s, %s)""",
            (real_session_id, answer, psycopg2.extras.Json(sources)),
        )
        cur.execute(
            "UPDATE support_chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (real_session_id,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

    return {
        "answer": answer,
        "sources": sources,
        "intent": intent,
        "session_id": real_session_id,
        "item_results": item_results,
    }
