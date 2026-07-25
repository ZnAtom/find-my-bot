# 智能客服设计说明

本文档描述当前第一阶段智能客服的实现思路。面向开发和维护，不会被直接导入为客服知识库；会被导入的是 `doc/support/` 下的 Markdown 文件。

## 1. 当前目标

智能客服覆盖三类问题：

| 场景 | 说明 |
| --- | --- |
| 平台使用问答 | 根据 FAQ、使用指南、登录说明、隐私说明等文档回答。 |
| 物品线索查找 | 根据用户描述在失物/招领物品库中查找相似记录。 |
| 个人数据查询 | 登录后查询自己的发布和认领申请摘要。 |

匿名用户可以使用基础客服，但会走匿名限流；登录用户可以额外查询自己的个人数据。

## 2. 入口与核心文件

| 模块 | 作用 |
| --- | --- |
| `frontend/src/components/SupportChatWidget.vue` | 前端悬浮客服窗口。 |
| `frontend/src/api/index.js` | `supportApi.chat()` 调用 `/api/support/chat`。 |
| `backend/app.py` | 暴露 `POST /api/support/chat`，做 CSRF、登录态、限流和错误转换。 |
| `backend/support.py` | 客服核心逻辑：意图识别、RAG、物品检索、个人数据、调用 LLM、保存会话。 |
| `backend/import_support_knowledge.py` | 将 `doc/support/*.md` 导入客服知识库。 |
| `backend/retrieval.py` | 物品搜索共用的 BM25L、向量过滤、RRF 和匹配度计算。 |

接口请求体：

```json
{
  "message": "我丢了一个学生证，请帮我寻找",
  "session_id": "可选",
  "channel": "web"
}
```

`channel` 目前允许 `web`、`qq`、`api`，为后续 QQ 群机器人复用同一套后端逻辑预留。

## 3. 数据表

客服相关表由 `backend/support.py` 的 `ensure_support_schema()` 创建：

| 表 | 作用 |
| --- | --- |
| `support_knowledge_sources` | 记录每个 Markdown 文件的路径、标题和内容哈希。 |
| `support_knowledge_chunks` | 文档切片，包含正文和可选 embedding JSONB。 |
| `support_chat_sessions` | 会话，绑定登录用户或匿名 key。 |
| `support_chat_messages` | 用户和客服消息历史，保存回答时的 sources。 |

知识库 embedding 当前存在 `support_knowledge_chunks.embedding JSONB` 中；物品库 embedding 存在 `lost_items.vector`，由 pgvector 查询。

## 4. 知识库同步

知识库来源目录：

```text
doc/support/
```

本地启动脚本默认启用：

```text
SUPPORT_AUTO_IMPORT=1
EMBEDDING_ENABLED=1
EMBEDDING_MODEL_PATH=model/models--Qwen--Qwen3-VL-Embedding-2B
```

因此执行下面命令时，会自动把 `doc/support/*.md` 同步进数据库：

```bash
bash dev-local.sh start
bash dev-local.sh restart
bash dev-local.sh db
```

同步是增量的：文件内容哈希没变且 embedding 不缺失时会跳过。手动强制重导入：

```bash
bash dev-local.sh support-import
```

## 5. 回答流程

`answer_support_chat()` 的流程：

1. 清理用户消息。
2. `detect_intent()` 判断意图。
3. 始终检索平台知识库，作为使用问答的 RAG 上下文。
4. 如果意图是 `item_search`，调用 `search_public_items()` 搜索物品库。
5. 如果意图是 `personal_data` 且用户已登录，加载自己的发布和申请摘要。
6. 将知识库、物品结果、个人数据组合成 prompt。
7. 调用学校兼容 OpenAI 格式的 LLM API。
8. 保存会话和消息，返回回答、意图、物品结果和 sources。

当前 LLM 配置：

| 环境变量 | 作用 |
| --- | --- |
| `SCHOOL_API_URL` | 学校 GenAI API 地址。 |
| `SCHOOL_API_KEY` | 学校 GenAI API key。 |
| `SUPPORT_LLM_MODEL` | 客服使用的模型，默认继承学校模型配置，当前本地使用 `GPT-5.5`。 |
| `SUPPORT_LLM_TIMEOUT_SECONDS` | 客服 LLM 超时时间。 |

## 6. 意图识别

当前是轻量规则识别：

| 意图 | 触发条件 | 后续行为 |
| --- | --- | --- |
| `personal_data` | 登录用户询问“我的发布、我的申请、我发过”等 | 查询自己的发布和申请。 |
| `item_search` | 出现“找、搜索、有没有、丢、捡到、招领、寻物、学生证、校园卡、耳机、钥匙”等 | 搜索物品库。 |
| `platform_help` | 其他情况 | 只根据知识库回答平台使用问题。 |

未登录用户询问个人数据时不会直接返回隐私信息，应引导登录后查看。

## 7. 物品库查询

客服物品查询现在和 `/api/semantic-search` 使用同一套混合检索思路：

1. 只查询 `status = 'active'` 的物品。
2. 同时覆盖寻物 `lost` 和招领 `found`，把方向写进候选摘要，避免替用户误判归属。
3. 若 `lost_items.vector` 存在、pgvector 可用、`EMBEDDING_ENABLED=1`，则用 Qwen embedding 编码用户问题并做向量召回。
4. 同时用 BM25L 做词法召回。
5. 用加权 RRF 融合向量召回和 BM25L 召回。
6. 用 `hybrid_match_score()` 计算展示匹配度，低于 `RESULT_RELEVANCE_THRESHOLD` 的候选丢弃。

例如“我丢了一个学生证，请帮我寻找”会命中数据库里的“红色封皮学生证”。客服 prompt 也要求：只要【物品搜索结果】非空，就必须列出候选物品，不能再说“没有线索”或“信息太少”。

## 8. 来源策略

前端“来源”区域不再显示知识库来源，也不显示个人数据来源。

| 问题类型 | sources 返回 |
| --- | --- |
| 平台使用问答 | 空数组，知识库只作为隐藏上下文。 |
| 个人数据查询 | 空数组，个人数据只作为隐藏上下文。 |
| 物品线索查找 | 只返回脱敏后的相关物品。 |

物品来源只包含：

- 编号和物品名。
- 寻物/招领方向。
- 状态。
- 分类。
- 地点摘要。
- 详情页入口。

客服和 sources 都不得直接输出手机号、QQ、邮箱、学号、证件号、二维码内容、条形码内容或完整姓名。

## 9. 限流与安全

`POST /api/support/chat` 会先做 CSRF 来源校验，再按登录态分桶限流：

| 环境变量 | 默认含义 |
| --- | --- |
| `SUPPORT_CHAT_ANON_RATE_LIMIT_COUNT` | 匿名用户窗口内最多请求数。 |
| `SUPPORT_CHAT_AUTH_RATE_LIMIT_COUNT` | 登录用户窗口内最多请求数。 |
| `SUPPORT_CHAT_RATE_LIMIT_WINDOW_SECONDS` | 限流窗口秒数。 |

匿名会话使用请求 IP 生成 hash，不直接存原始 IP。

## 10. 验证命令

运行客服单元测试：

```bash
backend/.venv/bin/python -m pytest backend/tests/test_support.py
```

启动或重启本地服务：

```bash
bash dev-local.sh restart
```

测试客服接口：

```bash
curl -sS \
  -H "Origin: http://localhost:5173" \
  -H "Content-Type: application/json" \
  -d '{"message":"我丢了一个学生证，请帮我寻找","channel":"web"}' \
  http://127.0.0.1:8000/api/support/chat
```

如果接口返回 502，先看 `backend` 日志区分是学校 LLM API 失败，还是本地后端未启动：

```bash
bash dev-local.sh status
tail -f .local/logs/backend.log
```
