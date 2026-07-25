"""
学校 GenAI API 测试脚本
测试意图：验证 API 调用格式是否正确，确保 agent.py 和 proxy.py 遵循学校 API 规范
"""
import asyncio
import httpx
import json
import os

from config_env import load_project_env

load_project_env()

# 学校 API 配置（与 agent.py 保持一致）
SCHOOL_API_URL = os.environ.get("SCHOOL_API_URL", "https://genaiapi.shanghaitech.edu.cn/api/v1/start")
SCHOOL_API_KEY = os.environ.get("SCHOOL_API_KEY")
SCHOOL_MODEL = os.environ.get("SCHOOL_MODEL", "qwen-instruct")


async def test_simple_chat():
    """测试基础对话调用"""
    print("=" * 60)
    print("测试 1: 基础对话调用")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SCHOOL_API_KEY}",
    }
    
    body = {
        "model": SCHOOL_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": "你是一个友好的助手。"},
            {"role": "user", "content": "你好，请介绍一下自己。"}
        ],
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0
    }
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(SCHOOL_API_URL, headers=headers, json=body)
            print(f"状态码: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"响应格式: {json.dumps(data, ensure_ascii=False, indent=2)[:1000]}")
                
                # 检查响应结构
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        print(f"\n模型回复: {content[:200]}")
                        return True
            else:
                print(f"错误响应: {resp.text[:500]}")
                
    except Exception as e:
        print(f"请求异常: {e}")
    
    return False


async def test_intent_classification():
    """测试意图识别"""
    print("\n" + "=" * 60)
    print("测试 2: 意图识别")
    print("=" * 60)
    
    test_cases = [
        ("你好", "chat"),
        ("有没有人捡到苹果耳机？", "search"),
        ("我丢了一个钱包，在图书馆丢的", "report_lost"),
        ("我捡到了一张校园卡", "report_found"),
        ("今天天气怎么样", "chat"),
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SCHOOL_API_KEY}",
    }
    
    system_prompt = """
你是一个校园失物招领系统的意图识别助手。请根据用户的消息判断意图类型。

意图类型定义：
1. chat：闲聊，与失物招领无关的日常对话，如问候、天气、闲聊等
2. search：查询，用户想查找失物信息，如"有没有人捡到手机"、"查找校园卡"
3. report_lost：挂失，用户丢失了物品，想要发布失物信息，如"我丢了一个钱包"、"挂失校园卡"
4. report_found：捡到，用户捡到了物品，想要发布招领信息，如"我捡到了一个手机"、"捡到钱包"
5. unknown：无法确定意图

请直接输出意图类型，不要输出其他内容。
    """.strip()
    
    success_count = 0
    
    for user_msg, expected_intent in test_cases:
        body = {
            "model": SCHOOL_MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 20,
            "presence_penalty": 1.5,
            "repetition_penalty": 1.0
        }
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(SCHOOL_API_URL, headers=headers, json=body)
                
                if resp.status_code == 200:
                    data = resp.json()
                    choice = data["choices"][0]
                    result = choice["message"]["content"].strip().lower()
                    
                    status = "✓" if result == expected_intent else "✗"
                    print(f"{status} 输入: '{user_msg}'")
                    print(f"   期望: {expected_intent}, 实际: {result}")
                    
                    if result == expected_intent:
                        success_count += 1
                else:
                    print(f"✗ 输入: '{user_msg}' - 请求失败")
                    
        except Exception as e:
            print(f"✗ 输入: '{user_msg}' - 异常: {e}")
    
    print(f"\n准确率: {success_count}/{len(test_cases)}")
    return success_count == len(test_cases)


async def test_information_extraction():
    """测试信息提取"""
    print("\n" + "=" * 60)
    print("测试 3: 信息提取（发布失物）")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SCHOOL_API_KEY}",
    }
    
    user_message = "我丢了一个黑色的苹果耳机，在图书馆三楼丢的，昨天下午丢的"
    
    extract_prompt = f"""
你是一个信息提取助手。请从用户的消息中提取以下信息：
物品名称、物品类型、地点、描述、时间、联系人、联系电话、联系QQ

用户消息：{user_message}
这是丢失信息。

请以 JSON 格式输出，字段包括：item_name, item_type, location, description, lost_time, contact_person, contact_phone, contact_qq
如果某个字段无法提取，请设为 null。
物品类型可选值：电子产品、证件卡片、衣物鞋帽、学习用品、其他
    """.strip()
    
    body = {
        "model": SCHOOL_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": extract_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0
    }
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(SCHOOL_API_URL, headers=headers, json=body)
            
            if resp.status_code == 200:
                data = resp.json()
                choice = data["choices"][0]
                result = choice["message"]["content"]
                
                print(f"原始输出:\n{result}")
                
                # 尝试解析 JSON（去掉 markdown 代码块标记）
                try:
                    # 去掉 ```json 和 ``` 标记
                    clean_result = result.strip()
                    if clean_result.startswith("```json"):
                        clean_result = clean_result[7:]
                    elif clean_result.startswith("```"):
                        clean_result = clean_result[3:]
                    if clean_result.endswith("```"):
                        clean_result = clean_result[:-3]
                    clean_result = clean_result.strip()
                    
                    parsed = json.loads(clean_result)
                    print(f"\n解析结果:")
                    print(f"  物品名称: {parsed.get('item_name')}")
                    print(f"  物品类型: {parsed.get('item_type')}")
                    print(f"  地点: {parsed.get('location')}")
                    print(f"  描述: {parsed.get('description')}")
                    print(f"  时间: {parsed.get('lost_time')}")
                    return True
                except json.JSONDecodeError:
                    print("\n✗ JSON 解析失败")
                    return False
            else:
                print(f"请求失败: {resp.text[:500]}")
                return False
                
    except Exception as e:
        print(f"请求异常: {e}")
        return False


async def test_proxy_endpoint():
    """测试本地 proxy 代理服务（需要先启动 proxy.py）"""
    print("\n" + "=" * 60)
    print("测试 4: 本地 Proxy 代理服务")
    print("=" * 60)
    
    proxy_url = "http://localhost:8001/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key",  # proxy 内部会替换为真实 key
    }
    
    body = {
        "model": "qwen-instruct",
        "stream": False,
        "messages": [
            {"role": "user", "content": "你好"}
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(proxy_url, headers=headers, json=body)
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"状态码: {resp.status_code}")
                print(f"响应格式: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                return True
            else:
                print(f"Proxy 请求失败: {resp.status_code} - {resp.text[:300]}")
                return False
                
    except httpx.ConnectError:
        print("✗ Proxy 服务未启动，请先运行: python proxy/proxy.py")
        return False
    except Exception as e:
        print(f"请求异常: {e}")
        return False


async def main():
    """运行所有测试"""
    print("学校 GenAI API 测试脚本")
    print("=" * 60)

    if not SCHOOL_API_KEY:
        print("缺少 SCHOOL_API_KEY 环境变量，跳过需要学校 GenAI API 的测试。")
        return
    
    results = []
    
    # 测试 1: 基础对话
    results.append(await test_simple_chat())
    
    # 测试 2: 意图识别
    results.append(await test_intent_classification())
    
    # 测试 3: 信息提取
    results.append(await test_information_extraction())
    
    # 测试 4: Proxy 服务（可选）
    results.append(await test_proxy_endpoint())
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print(f"通过: {sum(results)}/{len(results)}")
    print("=" * 60)
    
    if all(results):
        print("\n✓ 所有测试通过！")
    else:
        print("\n✗ 部分测试失败，请检查错误信息")


if __name__ == "__main__":
    asyncio.run(main())
