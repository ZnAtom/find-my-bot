"""
AI Agent 模块 - 手动工具调度模式
不依赖 function calling，通过 Prompt 让模型输出结构化 JSON，后端解析后调用工具
"""
import os
import json
import httpx
from typing import Optional, List, Dict, Any
from embedding import encode_text, encode_image
import psycopg2
import psycopg2.extras

# 学校 API 配置
SCHOOL_API_URL = os.environ.get("SCHOOL_API_URL", "https://genaiapi.shanghaitech.edu.cn/api/v1/start")
SCHOOL_API_KEY = os.environ.get("SCHOOL_API_KEY")
SCHOOL_MODEL = os.environ.get("SCHOOL_MODEL", "qwen-instruct")

# 数据库配置
DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "lostfound"),
    "user": os.environ.get("DB_USER", "appuser"),
    "password": os.environ.get("DB_PASSWORD", "password"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432")
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def serialize_row(row):
    """将 DictCursor 行转为 JSON 兼容的 dict"""
    if row is None:
        return None
    result = dict(row)
    for key, value in result.items():
        if hasattr(value, 'isoformat'):
            result[key] = value.isoformat()
        elif isinstance(value, bytes):
            result[key] = value.decode('utf-8')
    return result


# 数据库向量列维度（需与 pgvector column 定义一致，与 app.py 保持同步）
VECTOR_DIM = int(os.environ.get("VECTOR_DIM", "1536"))


def _vector_str(values: list[float]) -> str:
    trimmed = values[:VECTOR_DIM]
    return "[" + ",".join(str(v) for v in trimmed) + "]"


DIRECTION_ALIASES = {
    "lost": "lost",
    "find_item": "lost",
    "找物": "lost",
    "found": "found",
    "find_owner": "found",
    "找主": "found",
}

STATUS_ALIASES = {
    "active": "active",
    "pending": "active",
    "待匹配": "active",
    "recovered": "recovered",
    "resolved": "recovered",
    "matched": "recovered",
    "closed": "recovered",
    "已找回": "recovered",
    "expired": "expired",
    "过期": "expired",
}


def _coerce_direction(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return DIRECTION_ALIASES.get(value.strip())


def _coerce_status(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return STATUS_ALIASES.get(value.strip())


def _resolve_create_state(direction: Optional[str], status: Optional[str]) -> tuple[str, str]:
    resolved_direction = _coerce_direction(direction)
    legacy_direction = _coerce_direction(status)
    resolved_status = _coerce_status(status)

    if resolved_direction is None and legacy_direction is not None:
        resolved_direction = legacy_direction
    if resolved_direction is None:
        resolved_direction = "lost"
    if resolved_status is None:
        resolved_status = "active"

    return resolved_direction, resolved_status


def _apply_status_filter(where_clause: str, params: list, status: Optional[str]) -> str:
    status_direction = _coerce_direction(status)
    status_value = _coerce_status(status)
    if status_direction is not None:
        where_clause += " AND direction = %s AND status = 'active'"
        params.append(status_direction)
    elif status_value is not None:
        where_clause += " AND status = %s"
        params.append(status_value)
    return where_clause


# ========== 工具函数定义 ==========

def search_items(query: str, status: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
    """
    搜索失物招领信息
    :param query: 搜索关键词
    :param status: 状态过滤；兼容 lost/found 表示找物/找主，active/recovered/expired 表示生命周期
    :param limit: 返回数量限制
    :return: 搜索结果
    """
    try:
        vec = encode_text(query)
        vector_str = _vector_str(vec)
    except Exception:
        # 如果向量模型不可用，降级到关键字搜索
        return search_items_keyword(query, status, limit)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        where_clause = "WHERE vector IS NOT NULL"
        params = [vector_str, vector_str]
        
        if status:
            where_clause = _apply_status_filter(where_clause, params, status)
        
        cur.execute(
            f"""SELECT *, 1 - (vector <=> %s::vector) AS similarity
               FROM lost_items
               {where_clause}
               ORDER BY vector <=> %s::vector
               LIMIT %s""",
            params + [limit]
        )
        items = cur.fetchall()
        results = []
        for item in items:
            item_dict = serialize_row(item)
            # 移除向量字段，避免输出过大
            item_dict.pop('vector', None)
            results.append(item_dict)
        
        return {
            "success": True,
            "tool_name": "search_items",
            "results": results,
            "count": len(results)
        }
    finally:
        cur.close()
        conn.close()


def search_items_keyword(query: str, status: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
    """关键字搜索降级方案"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        where_clause = "WHERE 1=1"
        params = []
        
        if status:
            where_clause = _apply_status_filter(where_clause, params, status)
        
        where_clause += " AND (item_name ILIKE %s OR description ILIKE %s OR location ILIKE %s)"
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
        
        cur.execute(
            f"SELECT * FROM lost_items {where_clause} ORDER BY created_at DESC LIMIT %s",
            params + [limit]
        )
        items = cur.fetchall()
        results = []
        for item in items:
            item_dict = serialize_row(item)
            item_dict.pop('vector', None)
            results.append(item_dict)
        
        return {
            "success": True,
            "tool_name": "search_items",
            "results": results,
            "count": len(results)
        }
    finally:
        cur.close()
        conn.close()


def create_lost(item_name: str, item_type: str, location: str, 
                description: Optional[str] = None, lost_time: Optional[str] = None,
                contact_person: str = "匿名", contact_phone: Optional[str] = None,
                contact_qq: Optional[str] = None, status: Optional[str] = None,
                direction: Optional[str] = None) -> Dict[str, Any]:
    """
    创建失物招领信息
    :param item_name: 物品名称
    :param item_type: 物品类型
    :param location: 地点
    :param description: 描述
    :param lost_time: 丢失/捡到时间
    :param contact_person: 联系人
    :param contact_phone: 联系电话
    :param contact_qq: 联系QQ
    :param direction: 发布方向（lost=找物，found=找主）
    :param status: 生命周期状态（active/recovered/expired），兼容旧值 lost/found/pending/resolved
    :return: 创建结果
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    direction, item_status = _resolve_create_state(direction, status)
    
    # 构建向量
    try:
        vec = encode_text(f"{item_name} {description or ''}")
        vector_str = _vector_str(vec)
    except Exception:
        vector_str = None
    
    try:
        cur.execute(
            """INSERT INTO lost_items
               (item_name, item_type, description, location, lost_time, direction, status,
                contact_person, contact_phone, contact_qq, vector)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
            (item_name, item_type or "其他", description, location, lost_time, direction, item_status,
             contact_person, contact_phone, contact_qq, vector_str)
        )
        conn.commit()
        new_item = cur.fetchone()
        
        result = serialize_row(new_item)
        result.pop('vector', None)
        
        return {
            "success": True,
            "tool_name": "create_lost",
            "message": f"{'丢失' if direction == 'lost' else '捡到'}信息发布成功！",
            "item": result
        }
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "tool_name": "create_lost",
            "error": str(e)
        }
    finally:
        cur.close()
        conn.close()


def notify_match(item_id: int) -> Dict[str, Any]:
    """
    查询匹配记录
    :param item_id: 物品ID
    :return: 匹配结果
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # 查询该物品的匹配记录
        cur.execute(
            """SELECT mr.*, li.item_name as match_item_name, li.contact_person, li.contact_phone
               FROM match_records mr
               JOIN lost_items li ON mr.match_item_id = li.id
               WHERE mr.lost_item_id = %s OR mr.match_item_id = %s
               ORDER BY mr.similarity DESC""",
            (item_id, item_id)
        )
        matches = cur.fetchall()
        results = [serialize_row(m) for m in matches]
        
        return {
            "success": True,
            "tool_name": "notify_match",
            "matches": results,
            "count": len(results)
        }
    finally:
        cur.close()
        conn.close()


def get_banli(item_id: int) -> Dict[str, Any]:
    """
    查询办理进度
    :param item_id: 物品ID
    :return: 办理进度信息
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM lost_items WHERE id = %s", (item_id,))
        item = cur.fetchone()
        
        if not item:
            return {
                "success": False,
                "tool_name": "get_banli",
                "error": "物品不存在"
            }
        
        item_dict = serialize_row(item)
        item_dict.pop('vector', None)
        
        # 根据状态返回办理进度
        direction = item_dict.get("direction", "")
        status = item_dict.get("status", "")
        if status == "active" and direction == "lost":
            progress = "找物中：已登记，等待匹配..."
        elif status == "active" and direction == "found":
            progress = "找主中：已登记，等待失主联系..."
        elif status == "recovered":
            progress = "已找回：物品已被领取"
        elif status == "expired":
            progress = "已过期：记录不再参与匹配"
        else:
            progress = "未知状态"
        
        return {
            "success": True,
            "tool_name": "get_banli",
            "item": item_dict,
            "progress": progress
        }
    finally:
        cur.close()
        conn.close()


# ========== 工具调度映射 ==========

TOOLS_MAP = {
    "search_items": search_items,
    "create_lost": create_lost,
    "notify_match": notify_match,
    "get_banli": get_banli
}

TOOL_DESCRIPTIONS = {
    "search_items": {
        "name": "search_items",
        "description": "搜索失物招领信息，支持语义匹配",
        "parameters": {
            "query": {"type": "string", "description": "搜索关键词，如：手机、钱包、校园卡"},
            "status": {"type": "string", "description": "可选，旧值 lost/found 表示找物/找主；新值 active/recovered/expired 表示生命周期"},
            "limit": {"type": "integer", "description": "可选，返回数量，默认5"}
        }
    },
    "create_lost": {
        "name": "create_lost",
        "description": "发布失物或招领信息",
        "parameters": {
            "item_name": {"type": "string", "description": "物品名称，必填"},
            "item_type": {"type": "string", "description": "物品类型，如：电子产品、证件卡片、衣物鞋帽、学习用品、其他"},
            "location": {"type": "string", "description": "丢失或捡到地点，必填"},
            "description": {"type": "string", "description": "物品描述，可选"},
            "lost_time": {"type": "string", "description": "丢失或捡到时间，格式：YYYY-MM-DD HH:mm:ss，可选"},
            "contact_person": {"type": "string", "description": "联系人姓名，可选"},
            "contact_phone": {"type": "string", "description": "联系电话，可选"},
            "contact_qq": {"type": "string", "description": "联系QQ，可选"},
            "direction": {"type": "string", "description": "发布方向：lost(我丢了)或found(我捡到了)，默认lost"},
            "status": {"type": "string", "description": "可选，生命周期状态：active/recovered/expired"}
        }
    },
    "notify_match": {
        "name": "notify_match",
        "description": "查询物品的匹配记录，看看是否有相似的失物/招领信息",
        "parameters": {
            "item_id": {"type": "integer", "description": "物品ID，必填"}
        }
    },
    "get_banli": {
        "name": "get_banli",
        "description": "查询物品的办理进度",
        "parameters": {
            "item_id": {"type": "integer", "description": "物品ID，必填"}
        }
    }
}


# ========== LLM 调用 ==========

async def call_llm(messages: List[Dict[str, Any]]) -> str:
    """
    调用学校 GenAI API（遵循学校 API 文档规范）
    :param messages: 消息列表
    :return: 模型回复内容
    """
    if not SCHOOL_API_KEY:
        raise RuntimeError("缺少 SCHOOL_API_KEY 环境变量，无法调用学校 GenAI API")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SCHOOL_API_KEY}",
    }
    
    # 完全遵循学校 API 文档的请求格式
    body = {
        "model": SCHOOL_MODEL,
        "stream": False,
        "messages": messages,
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(SCHOOL_API_URL, headers=headers, json=body)
        
        if resp.status_code != 200:
            raise Exception(f"API调用失败: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        
        # 解析响应（遵循 OpenAI 兼容格式）
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice:
                message = choice["message"]
                # 返回文本内容
                if "content" in message and message["content"]:
                    return str(message["content"])
        
        raise Exception("API响应格式异常")


# ========== 意图识别 ==========

async def classify_intent(user_message: str) -> str:
    """
    意图识别：判断用户消息类型
    :param user_message: 用户消息
    :return: 意图类型：chat(闲聊) / search(查询) / report_lost(挂失) / report_found(捡到) / unknown(未知)
    """
    system_prompt = """
你是一个校园失物招领系统的意图识别助手。请根据用户的消息判断意图类型。

意图类型定义：
1. chat：闲聊，与失物招领无关的日常对话，如问候、天气、闲聊等
2. search：查询，用户想查找失物信息，如"有没有人捡到手机"、"查找校园卡"
3. report_lost：挂失，用户丢失了物品，想要发布失物信息，如"我丢了一个钱包"、"挂失校园卡"
4. report_found：捡到，用户捡到了物品，想要发布招领信息，如"我捡到了一个手机"、"捡到钱包"
5. unknown：无法确定意图

请直接输出意图类型，不要输出其他内容。
示例：
用户：你好
助手：chat

用户：有没有人捡到苹果耳机？
助手：search

用户：我丢了一个钱包，在图书馆丢的
助手：report_lost

用户：我捡到了一张校园卡
助手：report_found
"""
    
    messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_message}
    ]
    
    try:
        result = await call_llm(messages)
        return result.strip().lower()
    except Exception:
        return "unknown"


# ========== RAG 检索增强 ==========

def _format_item_state(item: Dict[str, Any]) -> str:
    status = item.get("status")
    direction = item.get("direction")
    if status == "recovered":
        return "已找回"
    if status == "expired":
        return "已过期"
    return "找主中" if direction == "found" else "找物中"


def build_rag_context(query: str, top_k: int = 5) -> str:
    """
    构建 RAG 上下文：从数据库检索相似记录
    :param query: 用户查询
    :param top_k: 返回数量
    :return: 格式化的上下文文本
    """
    try:
        search_result = search_items(query, limit=top_k)
        
        if not search_result.get("success") or search_result.get("count") == 0:
            return "（暂无相关失物信息）"
        
        items = search_result.get("results", [])
        context_lines = []
        
        for i, item in enumerate(items, 1):
            similarity = item.get("similarity", "")
            sim_str = f"（相似度: {similarity:.2%}）" if similarity else ""
            
            context_lines.append(
                f"{i}. 物品名称: {item.get('item_name', '')}{sim_str}\n"
                f"   类型: {item.get('item_type', '')}\n"
                f"   地点: {item.get('location', '')}\n"
                f"   状态: {_format_item_state(item)}\n"
                f"   描述: {item.get('description', '')[:50]}..." if item.get('description') else ""
            )
        
        return "\n".join(context_lines)
    
    except Exception:
        return "（检索服务暂时不可用）"


# ========== Agent 主循环 ==========

async def run_agent(user_message: str, max_tool_calls: int = 3) -> Dict[str, Any]:
    """
    运行 Agent 主循环
    :param user_message: 用户消息
    :param max_tool_calls: 最大工具调用次数
    :return: 最终回复
    """
    # 1. 意图识别
    intent = await classify_intent(user_message)
    print(f"[AGENT] 意图识别结果: {intent}")
    
    # 2. 根据意图处理
    if intent == "chat":
        # 闲聊：直接调用模型回复
        system_prompt = """
你是一个友好的校园失物招领助手。请用简短、友好的语气回答用户的问题。
如果用户询问失物招领相关的问题，请引导他们使用查询或发布功能。
        """
        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message}
        ]
        reply = await call_llm(messages)
        return {
            "intent": intent,
            "reply": reply,
            "tool_calls": [],
            "rag_context": ""
        }
    
    elif intent == "search":
        # 查询：先做 RAG 检索，再让模型生成回复
        rag_context = build_rag_context(user_message)
        
        system_prompt = f"""
你是一个校园失物招领助手。请根据以下检索到的失物信息，回答用户的查询。

检索到的相关信息：
{rag_context}

请用自然、友好的语言总结查询结果。
如果有匹配的失物，请列出详细信息（名称、地点、联系人）。
如果没有匹配的信息，请礼貌地告知用户。
        """
        
        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message}
        ]
        reply = await call_llm(messages)
        
        return {
            "intent": intent,
            "reply": reply,
            "tool_calls": [{"tool": "search_items", "query": user_message}],
            "rag_context": rag_context
        }
    
    elif intent in ["report_lost", "report_found"]:
        # 挂失/捡到：让模型提取关键信息，然后调用创建工具
        direction = "lost" if intent == "report_lost" else "found"
        
        extract_prompt = f"""
你是一个信息提取助手。请从用户的消息中提取以下信息：
物品名称、物品类型、地点、描述、时间、联系人、联系电话、联系QQ

用户消息：{user_message}
这是{'丢失' if direction == 'lost' else '捡到'}信息。

请以 JSON 格式输出，字段包括：item_name, item_type, location, description, lost_time, contact_person, contact_phone, contact_qq
如果某个字段无法提取，请设为 null。
物品类型可选值：电子产品、证件卡片、衣物鞋帽、学习用品、其他
        """
        
        messages = [
            {"role": "system", "content": extract_prompt.strip()},
            {"role": "user", "content": user_message}
        ]
        
        try:
            extract_result = await call_llm(messages)
            # 尝试解析 JSON（去掉 markdown 代码块标记）
            clean_result = extract_result.strip()
            if clean_result.startswith("```json"):
                clean_result = clean_result[7:]
            elif clean_result.startswith("```"):
                clean_result = clean_result[3:]
            if clean_result.endswith("```"):
                clean_result = clean_result[:-3]
            clean_result = clean_result.strip()
            
            try:
                data = json.loads(clean_result)
            except json.JSONDecodeError:
                # 如果不是 JSON，尝试从文本中提取
                data = {"item_name": user_message, "location": "未知", "item_type": "其他"}
            
            # 调用创建工具
            create_result = create_lost(
                item_name=data.get("item_name", ""),
                item_type=data.get("item_type", "其他"),
                location=data.get("location", "未知"),
                description=data.get("description"),
                lost_time=data.get("lost_time"),
                contact_person=data.get("contact_person", "匿名"),
                contact_phone=data.get("contact_phone"),
                contact_qq=data.get("contact_qq"),
                direction=direction
            )
            
            if create_result["success"]:
                reply = f"{create_result['message']}\n物品名称：{create_result['item']['item_name']}\n地点：{create_result['item']['location']}"
            else:
                reply = f"发布失败：{create_result.get('error', '未知错误')}"
            
            return {
                "intent": intent,
                "reply": reply,
                "tool_calls": [{"tool": "create_lost", "params": data}],
                "rag_context": "",
                "create_result": create_result
            }
        except Exception as e:
            return {
                "intent": intent,
                "reply": f"处理失败：{str(e)}",
                "tool_calls": [],
                "rag_context": ""
            }
    
    else:
        # 未知意图：询问用户
        reply = "我不太明白你的意思。请问你是要查询失物信息、发布丢失物品，还是发布捡到的物品？"
        return {
            "intent": "unknown",
            "reply": reply,
            "tool_calls": [],
            "rag_context": ""
        }
