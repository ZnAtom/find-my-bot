# 项目状态

本文档记录当前实现状态。最后更新基于当前服务器运行环境：Ubuntu 本地 PostgreSQL + FastAPI + Vite + nginx。通用部署步骤见 [getting-started.md](getting-started.md)，本服务器入口细节见 [server-local.md](server-local.md)。

## 1. 当前可运行服务

| 服务 | 地址 | 状态 |
| --- | --- | --- |
| 局域网入口 | `http://10.15.28.8/` | 可用 |
| 域名入口 | `http://foundit.geekpie.club/` | 服务端可用，依赖客户端 DNS/代理正确 |
| 前端 | `127.0.0.1:5173` | Vite 本地运行 |
| 后端 API | `127.0.0.1:8000` | FastAPI 本地运行 |
| API 文档 | `http://127.0.0.1:8000/docs` | FastAPI 自动生成 |
| 数据库 | `127.0.0.1:5432/lostfound` | 本地 PostgreSQL |
| nginx | `0.0.0.0:80` | 反向代理到前后端 |
| HTTPS | `:443` | 未配置 |
| QQ 机器人 | - | 预留，未接入 |

检查命令：

```bash
bash dev-local.sh status
ss -ltnp
```

## 2. 已完成

### 基础设施

- [X] Linux 本地开发脚本 `dev-local.sh`。
- [X] 本地 PostgreSQL 连接、schema 初始化和迁移。
- [X] pgvector 可选启用；当前本机已启用，`lost_items.vector VECTOR(1536)`。
- [X] HNSW 向量索引 `idx_lost_items_vector`，在向量列存在时自动创建。
- [X] FastAPI 后端本地后台启动，日志写入 `.local/logs/backend.log`。
- [X] Vue 3 + Vite 前端本地后台启动，日志写入 `.local/logs/frontend.log`。
- [X] nginx 80 端口反向代理，支持 `10.15.28.8` 和 `foundit.geekpie.club`。
- [X] Docker Compose 配置保留，支持 db/backend/frontend 编排和模型/文档挂载。
- [X] K8s 配置保留，包含 backend/frontend/db、Ingress、备份、数据清理和 NetworkPolicy。

### 数据库

- [X] `users` 表：Casdoor 绑定、角色、联系方式。
- [X] `lost_items` 表：寻物/招领、状态、地点、存放处、联系方式、图片、向量。
- [X] `claim_requests` 表：认领申请和联系申请。
- [X] `notifications` 表：站内通知和公告。
- [X] `match_records` 表：匹配记录预留。
- [X] `support_knowledge_sources` / `support_knowledge_chunks`：客服知识库。
- [X] `support_chat_sessions` / `support_chat_messages`：客服会话和消息。

### 后端 API

- [X] 登录：`/api/auth/login`、`/api/auth/callback`、`/api/auth/me`、`/api/auth/logout`。
- [X] 用户：`/api/users`、`/api/users/{id}`、`/api/me`。
- [X] 物品：`/api/lost-items` CRUD。
- [X] 上传：`POST /api/upload`，只允许图片类型和本站路径。
- [X] 图片识别：`POST /api/image-analysis`，调用学校 GPT-5.5。
- [X] 关键字搜索：`GET /api/search`。
- [X] 混合语义搜索：`GET /api/semantic-search`。
- [X] 发布前匹配：`POST /api/match-check`。
- [X] 认领/联系申请：`POST /api/lost-items/{id}/claim`、`GET /api/me/claims`、`GET /api/claim-requests`。
- [X] 通知：列表、未读数、标记已读、管理员发通知。
- [X] 智能客服：`POST /api/support/chat`。
- [X] 校园地图瓦片代理：`/api/campus-map/tiles/...`。

### AI / 检索

- [X] 本地 embedding：`Qwen/Qwen3-VL-Embedding-2B`，当前向量维度 1536。
- [X] embedding 默认启动启用：`EMBEDDING_ENABLED=1`。
- [X] 当前 `.env` 使用项目相对模型路径 `model/models--Qwen--Qwen3-VL-Embedding-2B`。
- [X] `HF_LOCAL_ONLY=1`，优先本地离线加载。
- [X] 物品向量：创建/更新时由名称、描述和图片生成。
- [X] 语义搜索：BM25L + pgvector + 加权 RRF + 展示匹配度过滤。
- [X] 客服物品查询：已与 `/api/semantic-search` 使用同类混合检索。
- [X] 查询扩展：校园卡/一卡通/学生卡/学生证/书籍类等。
- [X] 客服知识库 RAG：`doc/support/*.md` 自动同步，知识库 embedding 保存为 JSONB。
- [X] 图片识别：学校 GenAI API，模型 `GPT-5.5`，输出结构化 JSON。
- [X] 客服回答：学校 GenAI API，模型 `GPT-5.5`。

### 前端

- [X] Vue 3 + Vite + Element Plus SPA。
- [X] 首页、物品库、发布页、详情页、个人中心、管理页。
- [X] 登录态检查和路由守卫。
- [X] 图片上传和图片识别辅助填写。
- [X] 物品列表筛选、关键字搜索、语义搜索。
- [X] 认领/联系申请流程。
- [X] 通知展示。
- [X] 智能客服悬浮窗口。
- [X] 客服 sources 只展示物品来源，不展示知识库来源。

### 文档

- [X] [getting-started.md](getting-started.md)：当前 Linux 本地启动流程。
- [X] [architecture.md](architecture.md)：当前架构。
- [X] [search-retrieval.md](search-retrieval.md)：搜索、匹配和客服物品查询。
- [X] [support-chat.md](support-chat.md)：客服设计说明。
- [X] `doc/support/*.md`：客服用户知识库。

## 3. 待完成

### 产品功能

- [ ] QQ 群机器人实际接入：复用 `/api/support/chat`，使用 `channel=qq`。
- [ ] 账号与 QQ 身份绑定方案。
- [ ] 更完整的管理员审核和运营流程。
- [ ] 更细粒度的搜索筛选和排序策略。
- [ ] 搜索结果高亮。

### 匹配与通知

- [X] 发布前即时匹配 `POST /api/match-check`。
- [ ] `match_records` 自动落库和后台处理流程。
- [ ] 更稳定的主动匹配通知策略。
- [ ] 邮件/站内/QQ 多渠道通知编排。

### 部署

- [ ] HTTPS/443：当前域名只配置 HTTP。
- [ ] 生产 nginx 或前端静态构建托管方案。
- [ ] Docker Hub 网络不稳定时的镜像源/预拉取方案。
- [ ] Docker 内 embedding CPU 推理性能优化。
- [ ] 生产环境监控、日志聚合和告警。

### 数据与评估

- [X] 20 条校园失物/招领测试数据。
- [X] 物品向量补齐。
- [ ] 标注检索评测集。
- [ ] 客服回答质量评测集。
- [ ] 历史失物数据清洗导入。

## 4. 当前约束

- 当前域名 `foundit.geekpie.club` 解析到内网 IP `10.15.28.8`，公网设备无法直接访问。
- 当前未配置 HTTPS，浏览器必须使用 `http://`。
- 客服和图像识别依赖学校 GenAI API，外部 API 慢或失败时会影响回答。
- embedding 模型本地加载会占用较多内存，重启后首次加载较慢。
- 客服不会直接输出手机号、QQ、邮箱、学号、证件号、二维码内容、条形码内容或完整姓名。
