# 项目状态

## 已完成

### 基础设施

- [X] **PostgreSQL 16 + pgvector 容器化** — 根 `Dockerfile`，APT 安装 pgvector 0.8.4
- [X] **FastAPI 后端容器化** — `backend/Dockerfile`，启动时自动建表
- [X] **Vue 3 前端容器化** — `frontend/Dockerfile`，Vite dev server + HMR
- [X] **`docker-compose.yml` 一键编排** — db + backend + frontend，网络互通、健康检查、源码挂载热重载
- [X] **本地开发模式** — DB 用 Docker，后端本地跑用 MPS 加速，前端本地或 Docker

### 数据库

- [X] `users` 表 — 学号/姓名/联系方式
- [X] `lost_items` 表 — 物品名/类型/描述/地点/时间/状态/联系人/向量
- [X] `match_records` 表 — 匹配对/相似度/状态（预留，未接入逻辑）
- [X] pgvector `VECTOR(2048)` 列 + `<=>` 余弦距离算子
- [X] status、item_type 列 B-tree 索引（向量索引因维度超限暂未建）

### 后端 API

- [X] `GET/POST /api/users`、`GET /api/users/{id}` — 用户 CRUD
- [X] `GET/POST/PUT/DELETE /api/lost-items` — 失物 CRUD
- [X] `GET /api/search?query=` — 关键字 ILIKE 模糊搜索
- [X] `GET /api/semantic-search?query=` — 语义向量搜索（pgvector `<=>` 余弦距离）
- [X] `GET /api/stats` — 统计概览
- [X] 创建/更新失物时自动生成向量（`_build_vector → encode_text/encode_image → INSERT`）
- [X] 修正 `created_at`/`updated_at` 类型（str → datetime）

### AI / 向量化

- [X] `backend/embedding.py` — 模型管理 + 文本/图片编码
- [X] 接入 **Qwen/Qwen3-VL-Embedding-2B**（2048 维，约 4GB）
- [X] 设备自适应：MPS (Apple Silicon) > CUDA (NVIDIA) > CPU
- [X] 启动时预加载模型（FastAPI startup event），全局单例复用
- [X] HF 镜像 + `local_files_only` 离线模式
- [X] 使用 `sentence-transformers` + `torchvision`
- [X] 文本编码：`model.encode(text, normalize_embeddings=True)`
- [X] 图片编码：PIL 加载 → thumbnail(448,448) → `model.encode()`

### 前端

- [X] Vue 3 + Vite + Element Plus SPA，四个页面：
  - `HomePage` — 统计概览 + 最新失物
  - `LostListPage` — 失物列表 + 关键字/语义搜索双模式 + 相似度展示
  - `CreatePage` — 发布失物/招领
  - `AdminPage` — 管理后台（编辑/删除/标记找回 + 向量详情查看）
- [X] axios API 封装（`frontend/src/api/index.js`）
- [X] 语义搜索结果卡片显示相似度百分比徽章（颜色编码）

### 文档

- [X] `doc/getting-started.md` — 从零开始 Docker 启动教程
- [X] `doc/architecture.md` — 架构图、组件说明、数据流、API 文档
- [X] `README.md` — 项目一句话介绍 + 指向文档

---

## 待完成

### 核心功能缺口

- [ ] **智能匹配逻辑** — `match_records` 表已有但未接入代码。新建失物时应自动与现有失物做向量匹配，找到潜在配对（丢失 ↔ 捡到），写入 match_records
- [ ] **匹配通知** — 检测到高相似度匹配后通知相关用户（站内 / QQ / 邮箱）
- [ ] **图片上传** — 当前 `image_url` 字段支持但前端无上传功能；后端 `encode_image` 已就绪，缺文件上传端点
- [ ] **用户认证** — 无登录/注册/权限控制，任何人都能操作所有数据

### QQ 机器人

- [ ] QQ 机器人实际可运行 — NapCat 镜像拉取失败，需解决或更换方案
- [ ] AstrBot 对接后端 API — 群消息 → 语义搜索 → 回复结果
- [ ] QQ 群内失物发布流程 — 引导用户通过对话提交失物信息

### 前端体验

- [ ] 首页搜索框接入语义搜索（目前只跳转到列表页）
- [ ] CreatePage 物品类型改为动态分类
- [ ] 图片上传前端组件
- [ ] 失物详情页（点击卡片查看完整信息）
- [ ] 搜索结果高亮关键词

### 数据

- [ ] 初始数据导入 — 需要从微信群/QQ 群/校园墙爬取历史失物数据
- [ ] 向量索引 — pgvector 升级到支持 >2000 维索引的版本后建 HNSW 索引（数据量大时加速检索）
- [ ] 向量化质量评估 — 用标注数据测试匹配准确率

### 部署

- [ ] Docker 部署时模型可用 — 当前 Docker 内只有 CPU 推理，需将模型打入镜像或挂载
- [ ] 生产环境 compose file — 分离 dev/prod，前端改为 nginx 托管构建产物
- [ ] CI/CD — 自动构建、测试、部署
- [ ] 监控和日志 — 服务健康监控、异常告警

---

## 当前可运行的服务

| 服务      | URL                        | 状态                     |
| --------- | -------------------------- | ------------------------ |
| 前端      | http://localhost:5173      | 可用                     |
| 后端 API  | http://localhost:8000/api  | 可用                     |
| API 文档  | http://localhost:8000/docs | 可用（FastAPI 自动生成） |
| 数据库    | localhost:5432             | 可用                     |
| QQ 机器人 | —                         | 未启动                   |

启动方式：`docker compose up -d`（全部 Docker） 或 DB Docker + 后端/前端本地跑。
