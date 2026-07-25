# FoundIt

校园失物招领平台，支持寻物/招领发布、语义搜索、多图上传、AI 图片识别、认领流程、通知中心和管理员后台。

## 项目概览

FoundIt 当前是一个完整的前后端分离项目：

- 前端使用 Vue 3 + Vite + Element Plus，提供首页、列表、详情、发布、个人中心和管理台。
- 后端使用 FastAPI + PostgreSQL + pgvector，负责认证、记录管理、语义检索、图片上传、通知和认领流程。
- 向量检索使用 `Qwen/Qwen3-VL-Embedding-2B`，支持文本和图片混合编码，数据库侧使用 pgvector HNSW 索引。
- 图片自动填表接入上海科技大学 GenAI 图像理解接口。
- 部署层同时提供 Docker Compose 本地方案和 `k8s/` 生产清单。

## 当前功能

- 寻物和招领双流程发布。
- 关键词搜索和语义搜索。
- 多张图片上传，并基于图片自动提取物品名称、分类和描述。
- 详情页按权限显示联系方式，支持 `private`、`logged_in`、`claimed`、`public` 四种可见性。
- 登录用户可提交认领或联系申请，系统自动生成站内通知。
- Casdoor OAuth 登录、个人资料维护、我的发布列表。
- 管理员后台支持物品管理、用户角色管理、申请查看和系统通知发送。
- 校园地点选择和校园地图瓦片代理。
- 可选 QQ 机器人目录与 compose 预留配置。

## 技术栈

- 前端：Vue 3、Vue Router、Pinia、Element Plus、Axios、Vitest
- 后端：FastAPI、Uvicorn、psycopg2、Sentence Transformers、PyTorch
- 数据库：PostgreSQL 16、pgvector
- 部署：Docker Compose、Kubernetes、ArgoCD 清单

## 目录结构

```text
.
|-- backend/        FastAPI 服务、数据库 schema、迁移脚本、测试
|-- frontend/       Vue 3 前端应用
|-- doc/            架构、接口、部署、业务流程等补充文档
|-- k8s/            Kubernetes 部署与运维清单
|-- proxy/          辅助代理脚本
|-- qqbot/          NapCat / AstrBot 预留配置
|-- docker-compose.yml
|-- .env.example
|-- .env.server.example
|-- dev-local.sh
`-- README.md
```

## 快速开始

### 1. 准备环境

- Docker Desktop 或 Docker Engine + Docker Compose
- 如果要本地运行前后端而不是全量 Docker：
  - Python 3.12+
  - Node.js 22+

### 2. 配置环境变量

复制模板：

```bash
cp .env.example .env
```

`.env.example` 面向任意本地开发设备，默认不启用 embedding，方便先跑通服务。`.env.server.example` 是局域网/域名部署形态的参考模板，包含 nginx 同域反代、宿主机 PostgreSQL 和本地 Qwen 模型的配置示例，但仍需要替换密钥和具体域名/IP。

建议至少确认以下配置：

| 变量 | 用途 |
| --- | --- |
| `CASDOOR_CLIENT_ID` / `CASDOOR_CLIENT_SECRET` | Casdoor 登录 |
| `CASDOOR_REDIRECT_URI` | OAuth 回调地址 |
| `FRONTEND_BASE_URL` | 前端访问地址 |
| `JWT_SECRET` | 会话签名密钥，至少 32 字符 |
| `SCHOOL_API_KEY` | 图片识别服务 |
| `CORS_ORIGINS` | CORS 白名单 |
| `CSRF_TRUSTED_ORIGINS` | CSRF 来源白名单 |

说明：

- 只想先跑匿名浏览、列表和基础发布，认证相关变量可以后补。
- 本地 Docker 暂时不跑千问 embedding 时，保持 `INSTALL_EMBEDDING_DEPS=0` 和 `EMBEDDING_ENABLED=0`；发布记录的 `vector` 会为空，`/api/semantic-search` 会退回 BM25 检索。
- 要使用登录、个人中心、管理员后台，必须正确配置 Casdoor 和 `JWT_SECRET`。
- 要使用 AI 图片识别，必须配置 `SCHOOL_API_KEY`。

### 3. 使用 Docker Compose 启动

```bash
docker compose up -d --build
```

服务地址：

| 服务 | 地址 |
| --- | --- |
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000/api |
| FastAPI 文档 | http://localhost:8000/docs |
| PostgreSQL | `127.0.0.1:5433` |

启动时会自动执行：

- `backend/schema.sql`
- `backend/migrate_auth.py`
- `backend/migrate_item_state.py`
- `backend/migrate_flow_fields.py`

默认本地配置 `INSTALL_EMBEDDING_DEPS=0`、`EMBEDDING_ENABLED=0`，后端镜像不会安装 embedding 相关依赖，也不会加载 `Qwen/Qwen3-VL-Embedding-2B`，基础浏览、发布、关键词检索和 BM25 召回可用。后续需要启用向量语义搜索时，将 `.env` 中这两项都改为 `1` 后重新构建并启动后端；首次启动可能需要下载模型，耗时取决于网络和机器性能。

## 本地开发

### Linux 一键本地启动

Linux 本地开发推荐使用 `dev-local.sh`：数据库用 Docker Compose 的 `db` 服务，后端和前端直接跑在宿主机，方便热重载。

先安装系统依赖：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip docker.io docker-compose-plugin postgresql-client psmisc gettext-base
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

还需要安装 Node.js 22+ 和 npm，推荐用 `nvm` 或 NodeSource；部分 Ubuntu 源里的 `nodejs` 版本偏旧。执行 `usermod` 后需要退出当前 shell 并重新登录，或者临时用 `sudo docker ...` 验证 Docker。

初始化 Python/Node 依赖：

```bash
cd find-my-bot
bash dev-local.sh setup
```

启动全部服务：

```bash
bash dev-local.sh start
```

常用命令：

```bash
bash dev-local.sh status
bash dev-local.sh logs
bash dev-local.sh restart
bash dev-local.sh stop
```

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端文档：`http://127.0.0.1:8000/docs`
- 数据库：`127.0.0.1:5433/lostfound`

默认本地脚本保持 `EMBEDDING_ENABLED=0`，不会加载 Qwen embedding；图片识别仍使用学校 GenAI API 的 `SCHOOL_API_KEY` 和 `SCHOOL_VISION_MODEL`。

如果模型目录已经在项目内，推荐使用相对路径：

```text
EMBEDDING_MODEL_PATH=model/models--Qwen--Qwen3-VL-Embedding-2B
SUPPORT_DOCS_DIR=doc/support
```

需要类似当前服务器的局域网/域名部署时，可以先复制服务器模板再按实际环境修改：

```bash
cp .env.server.example .env
```

如果 Docker Hub 拉取 PostgreSQL 镜像仍然超时，也可以改用本机 PostgreSQL 16 + pgvector。先创建用户和数据库，然后用 `DB_MODE=local` 启动：

```bash
DB_MODE=local DB_PORT=5432 bash dev-local.sh start
```

### 手动启动

不用脚本时，顺序是：

1. 启动 PostgreSQL，并确保已安装 `pgvector` 扩展。
2. 在项目根目录配置 `.env`。
3. 在 `backend/` 安装依赖并运行 `python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload`。
4. 在 `frontend/` 执行 `npm install` 和 `npm run dev`。

开发环境下，Vite 会把 `/api` 和 `/uploads` 代理到 `http://127.0.0.1:8000`。

## 搜索与匹配逻辑

系统保留三种搜索路径：

- `/api/search`：基础关键词搜索，使用 PostgreSQL `ILIKE`，用于简单检索和效果对照。
- `/api/semantic-search`：面向搜索页的 BM25L + 向量混合检索。
- `/api/match-check`：发布前匹配，仅检索相反发布方向的有效记录，并在混合召回后做规则重排。

混合检索的执行过程：

1. 仅将物品名称、分类和描述组合为搜索文本，其中物品名称和分类会提高词频权重。搜索不使用丢失地点或存放地点。
2. 使用 `jieba` 分词，并补充中文单字和双字词元；校园卡、一卡通、校园一卡通和学生卡会进行双向领域同义词扩展。
3. BM25L 分支对精确词汇进行排序并召回最多 10 条。BM25L 是适合当前小规模校园数据集的 BM25 变体，可避免极小语料下 Okapi BM25 的零 IDF 问题。
4. 向量分支使用 `Qwen/Qwen3-VL-Embedding-2B` 和 pgvector 余弦距离召回最多 10 条，用于补充同义词和语义相近表达。向量只编码物品名称、描述和图片，不编码地点或时间；低于绝对阈值或与头部结果差距过大的候选会被剔除。
5. 两路结果使用加权 RRF 融合。默认 BM25L 权重为 `0.7`，向量权重为 `0.3`，因此精确词汇命中优先级更高。
6. `/api/match-check` 还会对物品分类完全一致、名称词重合和地点词重合的记录进行轻量加分。
7. 最终最多返回 10 条结果，但不会为了凑满 10 条而返回低相关物品；数据库向量属于内部字段，不会返回给前端。

相关参数位于 `.env`：

| 变量 | 默认值 | 说明 |
| --- | ---: | --- |
| `BM25_WEIGHT` | `0.7` | BM25L 在加权 RRF 中的权重 |
| `VECTOR_WEIGHT` | `0.3` | 向量召回在加权 RRF 中的权重 |
| `RETRIEVAL_CANDIDATE_LIMIT` | `10` | 每个召回分支的候选数，程序上限为 10 |
| `VECTOR_SIMILARITY_THRESHOLD` | `0.48` | 向量候选最低余弦相似度 |
| `VECTOR_SIMILARITY_MAX_DROP` | `0.08` | 候选相对最佳向量结果允许的最大分差 |
| `RESULT_RELEVANCE_THRESHOLD` | `0.65` | 最终展示结果的最低综合匹配度 |

修改向量编码字段后，可在本地重建全部历史记录的内容向量：

```bash
conda activate hugging_face
cd backend
python rebuild_content_vectors.py
```

## 业务规则

- 发布寻物记录需要登录，并至少提供一种联系方式。
- 发布招领记录必须填写当前存放处。
- 匿名用户可以发布招领，但不能填写联系方式，且发布后不能自行编辑或删除。
- 记录图片只能使用本站 `/uploads` 目录下已上传的文件，不能直接引用第三方图片 URL。
- 发布前前端会调用 `/api/match-check` 做一次相似记录提示。
- 联系方式默认受权限控制，只有满足可见条件的用户才能看到完整信息。

## 测试

### 搜索测试数据

本地数据库可以插入 56 条带向量的搜索样本，覆盖一卡通、手机、水杯、钥匙、耳机、雨伞、背包、书籍、电脑、钱包、衣物、学生证、智能手表、眼镜、存储设备、实验用品、运动器材、行李、首饰和平板等，并同时提供寻物与招领方向：

```bash
conda activate hugging_face
cd backend
python seed_search_test_data.py
```

脚本可重复执行，已存在的样本会自动跳过。只删除该脚本创建的数据：

```bash
python seed_search_test_data.py --clean
```

不加载嵌入模型、只插入用于 BM25 测试的记录：

```bash
python seed_search_test_data.py --without-vectors
```

前端：

```bash
cd frontend
npm test
```

后端：

```bash
cd backend
pytest
```

## 部署与运维

### Docker Compose

适合本地开发、演示和联调，根目录 `docker-compose.yml` 默认启动：

- `db`
- `backend`
- `frontend`

### Kubernetes

`k8s/` 目录已包含以下资源：

- `backend.yaml`、`frontend.yaml`、`db.yaml`
- `ingress.yaml`
- `db-network-policy.yaml`
- `db-backup.yaml`
- `data-retention-cronjob.yaml`
- `argocd-app.yaml`

### QQ 机器人

根目录 `docker-compose.yml` 中预留了 `napcat` 和 `astrbot` 配置，默认注释。相关文件位于 `qqbot/`。

## 常用命令

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
docker compose down -v
docker compose exec db psql -U appuser -d lostfound
```

## 相关文档

- [快速部署指南](doc/getting-started.md)
- [架构设计](doc/architecture.md)
- [搜索与匹配计算说明](doc/search-retrieval.md)
- [接口说明](doc/api.md)
- [数据库与安全策略](doc/database-security.md)
- [业务流程梳理](doc/业务流程梳理.md)

## License

本项目基于 [MIT License](LICENSE) 开源。
