"""
轻量 API 代理：将 OpenAI 标准路径重定向到学校 GenAI API
学校 API 已兼容 OpenAI 格式，只需路径映射
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import json
import os

app = FastAPI()

SCHOOL_API_URL = os.environ.get("SCHOOL_API_URL", "https://genaiapi.shanghaitech.edu.cn/api/v1/start")
SCHOOL_API_KEY = os.environ.get("SCHOOL_API_KEY")
SCHOOL_MODEL = os.environ.get("SCHOOL_MODEL", "qwen-instruct")


# 学校 API 不支持的字段，需要过滤
UNSUPPORTED_FIELDS = {"tools", "tool_choice", "response_format", "parallel_tool_calls", "function_call"}

def sanitize_body(body: dict) -> dict:
    """移除学校 API 不支持的字段，强制设置正确的 model"""
    filtered = {k: v for k, v in body.items() if k not in UNSUPPORTED_FIELDS}
    # 强制覆盖 model 为学校 API 正确的模型名
    filtered["model"] = SCHOOL_MODEL
    # 也过滤 messages 中 message 级别的 tool_calls 和 tool_call_id
    if "messages" in filtered:
        for msg in filtered["messages"]:
            msg.pop("tool_calls", None)
            msg.pop("tool_call_id", None)
    return filtered


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    if not SCHOOL_API_KEY:
        raise HTTPException(status_code=500, detail="缺少 SCHOOL_API_KEY 环境变量，无法调用学校 GenAI API")

    body = await request.json()
    stream = body.get("stream", False)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SCHOOL_API_KEY}",
    }

    # 过滤不支持的字段
    filtered_body = sanitize_body(body)

    print(f"[PROXY] Incoming request: model={body.get('model')}, stream={stream}, messages_count={len(body.get('messages', []))}", flush=True)
    print(f"[PROXY] Filtered body keys: {list(filtered_body.keys())}", flush=True)

    async with httpx.AsyncClient(timeout=120) as client:
        if stream:
            resp = await client.post(SCHOOL_API_URL, headers=headers, json=filtered_body)
            print(f"[PROXY] Stream response status: {resp.status_code}", flush=True)
            if resp.status_code != 200:
                error_text = await resp.aread()
                raise HTTPException(status_code=resp.status_code, detail=error_text.decode())

            return StreamingResponse(
                resp.aiter_raw(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        else:
            resp = await client.post(SCHOOL_API_URL, headers=headers, json=filtered_body)
            print(f"[PROXY] Non-stream response status: {resp.status_code}, body: {resp.text[:200]}", flush=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            # 清理响应中的 tool_calls 字段，避免 AstrBot 的 OpenAI SDK 解析失败
            data = resp.json()
            if "choices" in data:
                for choice in data["choices"]:
                    if "message" in choice and "tool_calls" in choice["message"]:
                        del choice["message"]["tool_calls"]
            return data


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": SCHOOL_MODEL,
                "object": "model",
                "created": 0,
                "owned_by": "shanghaitech"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
