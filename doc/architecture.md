# 项目架构与运行流程

本文档描述 FoundIt 校园失物招领平台的通用架构。默认本地运行模式是 Docker Compose 数据库 + 宿主机 FastAPI + 宿主机 Vite；需要无端口访问时再用 nginx 反向代理。当前服务器的具体 IP/域名记录见 [server-local.md](server-local.md)。

## 1. 通用运行拓扑

```text
浏览器
  │
  │ http://127.0.0.1:5173/          # 默认本机开发
  │ http://your-host.example/       # 可选 nginx 同域入口
  ▼
Vite dev server 或 nginx :80
  ├── /api/*      -> FastAPI 127.0.0.1:8000
  ├── /uploads/*  -> FastAPI 127.0.0.1:8000
  └── 其他路径     -> Vite 127.0.0.1:5173

FastAPI backend
  ├── Casdoor OAuth 登录
  ├── 图片上传与学校 GPT-5.5 图像识别
  ├── 物品 CRUD、认领/联系申请、通知
  ├── 搜索与匹配：BM25L + Qwen embedding + pgvector + RRF
  └── 智能客服：RAG + 物品搜索 + 登录用户个人数据

PostgreSQL
  ├── users / lost_items / claim_requests / notifications
  ├── support_knowledge_* / support_chat_*
  └── pgvector: lost_items.vector VECTOR(1536)
```

默认本地服务监听状态应类似：

| 服务 | 监听地址 | 说明 |
| --- | --- | --- |
| nginx | `0.0.0.0:80` | 可选局域网入口和反向代理 |
| frontend | `127.0.0.1:5173` | Vite dev server |
| backend | `127.0.0.1:8000` | FastAPI |
| PostgreSQL | `127.0.0.1:5433` | 默认 Docker 数据库 |

如果没有配置 443 和证书，浏览器必须使用 `http://`，不要访问 `https://...`。

## 2. 核心组件

| 组件 | 技术 | 职责 |
| --- | --- | --- |
| Frontend | Vue 3 + Vite + Element Plus | 单页应用、物品库、发布页、个人中心、管理页、客服窗口 |
| Backend | FastAPI + psycopg2 | REST API、权限、上传、搜索、图像识别、客服 |
| Database | PostgreSQL + pgvector | 结构化数据和物品向量检索 |
| Embedding | `Qwen/Qwen3-VL-Embedding-2B` | 本地文本/图文向量，当前维度 1536 |
| Vision LLM | 学校兼容 OpenAI 格式 API，模型 `GPT-5.5` | 图片识别辅助填写表单 |
| Support LLM | 学校兼容 OpenAI 格式 API，模型 `GPT-5.5` | 智能客服生成回答 |
| nginx | nginx 1.18 | 80 端口入口，隐藏 5173/8000 端口 |
| QQ Bot | 预留 | 未来通过 `channel=qq` 调用同一套客服后端 |

## 3. 启动流程

推荐使用项目脚本：

```bash
bash dev-local.sh setup      # 首次安装依赖
bash dev-local.sh start      # 启动 db 检查、schema、知识库同步、后端、前端
bash dev-local.sh restart    # 重启本地服务
bash dev-local.sh status     # 查看状态
```

`dev-local.sh start/restart/db` 会自动执行：

1. 加载 `.env`。
2. 检查 PostgreSQL 可连接。
3. 执行 `backend/schema.sql` 和迁移脚本。
4. 在 `SUPPORT_AUTO_IMPORT=1` 时同步 `doc/support/*.md` 到客服知识库。
5. 启动后端和前端。

通用模板默认不启用 embedding，方便新设备先跑通服务；需要向量检索时再显式启用：

```text
EMBEDDING_ENABLED=1
HF_LOCAL_ONLY=1
EMBEDDING_MODEL_PATH=model/models--Qwen--Qwen3-VL-Embedding-2B
VECTOR_DIM=1536
```

## 4. 数据表概览

### users

| 字段 | 说明 |
| --- | --- |
| `student_id` / `name` | 校园用户身份信息 |
| `phone` / `qq` / `email` | 联系方式，按权限控制展示 |
| `casdoor_sub` / `casdoor_name` | Casdoor OAuth 绑定信息 |
| `role` | `user` 或管理员角色 |

### lost_items

| 字段 | 说明 |
| --- | --- |
| `item_name` / `item_type` / `description` | 搜索和展示核心字段 |
| `location` / `storage_location` | 丢失/捡到地点和招领存放处 |
| `lost_time` / `found_time` | 时间信息 |
| `direction` | `lost` 寻物或 `found` 招领 |
| `status` | `active`、`recovered`、`expired` |
| `contact_visibility` | 联系方式可见性策略 |
| `image_url` | 本站 `/uploads/` 图片路径 |
| `vector` | `VECTOR(1536)`，物品内容向量 |

### claim_requests / notifications

- `claim_requests` 保存认领申请和联系申请。
- `notifications` 保存站内通知、系统公告和申请提醒。

### support tables

| 表 | 说明 |
| --- | --- |
| `support_knowledge_sources` | 客服知识库 Markdown 文件索引 |
| `support_knowledge_chunks` | 文档切片和知识库 embedding |
| `support_chat_sessions` | 客服会话 |
| `support_chat_messages` | 客服消息和 sources 快照 |

## 5. 搜索与向量管道

创建或更新物品时，如果 embedding 启用且 `lost_items.vector` 存在：

```text
物品名称 + 描述 + 图片
  -> Qwen3-VL-Embedding-2B
  -> 1536 维归一化向量
  -> lost_items.vector
```

搜索分为三条路径：

| 场景 | 入口 | 逻辑 |
| --- | --- | --- |
| 关键字搜索 | `GET /api/search` | PostgreSQL `ILIKE` |
| 混合搜索 | `GET /api/semantic-search` | BM25L + pgvector + RRF + 匹配度阈值 |
| 发布前匹配 | `POST /api/match-check` | 只匹配相反方向物品，并做规则重排 |

智能客服在识别为物品查询时，调用 `backend/support.py::search_public_items()`，使用和 `/api/semantic-search` 同类的混合检索逻辑。详见 [search-retrieval.md](search-retrieval.md)。

## 6. 图片识别

图片上传后保存在 `backend/uploads/`，对外通过 `/uploads/*` 提供静态访问。

图片识别接口：

```text
POST /api/image-analysis
```

当前逻辑：

1. 只接受本站上传图片路径或受控远程图片 URL。
2. 后端用 PIL 统一方向、压缩为 JPEG，并控制最大边长和请求体大小。
3. 调用学校 GenAI API 的 `GPT-5.5`。
4. 要求模型输出严格 JSON：`item_name`、`item_type`、`description`、`notes`。
5. 不输出完整姓名、手机号、QQ、学号、证件号、二维码或条形码内容。

## 7. 智能客服

客服入口：

```text
POST /api/support/chat
```

客服流程：

1. CSRF 来源校验。
2. 登录态识别和限流。
3. 规则判断意图：平台帮助、物品查询、个人数据。
4. 始终检索 `doc/support/*.md` 知识库作为隐藏 RAG 上下文。
5. 物品查询时走混合检索，返回脱敏物品候选。
6. 登录用户询问个人数据时读取自己的发布和申请摘要。
7. 调用学校 GPT-5.5 生成简短回答。

前端“来源”策略：

- 平台知识库来源不展示。
- 个人数据来源不展示。
- 只有物品查询显示脱敏物品来源。

详见 [support-chat.md](support-chat.md)。

## 8. 认证与访问控制

登录使用 Casdoor OAuth：

| 路径 | 说明 |
| --- | --- |
| `GET /api/auth/login` | 生成登录跳转 |
| `GET /api/auth/callback` | 处理 OAuth 回调 |
| `GET /api/auth/me` | 当前登录用户 |
| `POST /api/auth/logout` | 退出登录 |

域名访问时，Casdoor 后台必须允许实际回调地址，例如：

```text
http://your-host.example/api/auth/callback
```

跨设备访问需要同时配置：

- `FRONTEND_BASE_URL`
- `CASDOOR_REDIRECT_URI`
- `CORS_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- nginx `server_name`

## 9. Docker 与 K8s

Docker 配置仍保留：

- `docker-compose.yml` 编排 db/backend/frontend。
- db 服务暴露到 `127.0.0.1:5433`。
- backend/frontend 也只绑定本机端口，适合再由 nginx 或其他入口代理。
- backend 可通过挂载 `./model` 使用本地 embedding 模型。

K8s 配置位于 `k8s/`，包含 backend/frontend/db、Ingress、备份、数据清理和 NetworkPolicy。它是生产部署方向，但当前本机调试不依赖 K8s。

## 10. 目录结构

```text
find-my-bot/
├── dev-local.sh                 # Linux 本地开发脚本
├── docker-compose.yml           # Docker 编排
├── deploy/nginx/                # 本地域名 nginx 配置
├── backend/
│   ├── app.py                   # FastAPI 主入口
│   ├── support.py               # 智能客服核心
│   ├── retrieval.py             # BM25L/向量/RRF/匹配度
│   ├── embedding.py             # Qwen embedding 加载与编码
│   ├── schema.sql               # 数据库 schema
│   └── uploads/                 # 上传图片
├── frontend/
│   └── src/
│       ├── api/index.js
│       └── components/
├── doc/
│   ├── support/                 # 客服用户知识库，会自动导入
│   ├── support-chat.md          # 客服开发说明
│   └── search-retrieval.md      # 检索说明
├── k8s/
└── model/
    └── models--Qwen--Qwen3-VL-Embedding-2B
```
