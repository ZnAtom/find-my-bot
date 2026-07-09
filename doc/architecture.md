# 项目架构与运行流程

## 整体架构

```
┌────────────────────────────────────────────────────────────┐
│                       用户入口                              │
│  浏览器 (:5173)              QQ 机器人 (计划中)              │
└─────────┬──────────────────────────┬───────────────────────┘
          │                          │
          ▼                          ▼
┌─────────────────┐     ┌─────────────────────┐
│   frontend      │     │  qqbot (计划中)      │
│   Vue 3 + Vite  │     │  NapCat + AstrBot   │
│   Element Plus  │     │  OneBot v11 协议     │
└────────┬────────┘     └──────────┬──────────┘
         │                         │
         │  HTTP REST API          │
         ▼                         ▼
┌─────────────────────────────────────────────┐
│                backend :8000                │
│              FastAPI (Python)               │
│                                             │
│  ┌──────────────┐  ┌────────────────────┐   │
│  │  CRUD 端点   │  │  embedding 模块    │   │
│  │  /api/users  │  │  Qwen3-VL-Emb-2B   │   │
│  │  /api/lost-  │  │  2048 维向量       │   │
│  │   items      │  │  MPS/CUDA/CPU      │   │
│  └──────┬───────┘  └────────┬───────────┘   │
│         │                   │                │
└─────────┼───────────────────┼────────────────┘
          │                   │
          ▼                   ▼
┌─────────────────────────────────────────────┐
│                db :5432                     │
│        PostgreSQL 16 + pgvector             │
│                                             │
│  users │ lost_items │ match_records         │
│                │                            │
│        vector VECTOR(2048)                  │
│        <=> 余弦距离算子                      │
└─────────────────────────────────────────────┘
```

## 组件速览

| 组件               | 技术                        | 职责                       |
| ------------------ | --------------------------- | -------------------------- |
| **frontend** | Vue 3 + Vite + Element Plus | Web 管理后台，四个页面     |
| **backend**  | FastAPI + psycopg2          | REST API，向量化，业务逻辑 |
| **db**       | PostgreSQL 16 + pgvector    | 数据存储，向量相似度检索   |
| **qqbot**    | NapCat + AstrBot（计划中）  | QQ 群失物查询入口          |

## 启动流程

### Docker 模式（`docker compose up -d`）

```
1. docker compose 读取 docker-compose.yml
2. 构建镜像（首次或 --build 时）
   ├── db:     根 Dockerfile → postgres:16 + pgvector (APT)
   ├── backend: backend/Dockerfile → python:3.12 + requirements.txt
   └── frontend: frontend/Dockerfile → node:22 + npm install
3. 创建网络 app-network、数据卷 pgdata
4. 按依赖顺序启动：
   db → (健康检查通过) → backend → frontend
5. backend/entrypoint.sh：
   a. 等待 db:5432 可通
   b. psql 执行 schema.sql 建表
   c. 启动 uvicorn app:app --reload
```

### Kubernetes (GitOps) 模式

```
1. 开发者 git push 推送代码至 GitHub
2. GitHub Actions 构建三个容器镜像 (db, backend, frontend) 推送至 ghcr.io
3. GitHub Actions 更新 k8s/kustomization.yaml 中的镜像 tag，并自动提交
4. ArgoCD 监听 Git 仓库变更，同步资源至 K8s 集群
5. K8s 创建新 Pod (Frontend, Backend, DB)
6. Backend Pod 启动：
   a. 等待 DB 连接就绪并执行 schema 建表
   b. 等待 Qwen 模型下载完毕 (HF_ENDPOINT 加速)
   c. 就绪探针 (readinessProbe) 检查 /docs 成功后，Nginx Ingress 放行流量
```

### 本地开发模式

```bash
# 数据库仍用 Docker
docker compose up -d db

# 后端本地运行（可用 MPS 加速）
cd backend
pip install -r requirements.txt
python3 app.py

# 前端本地运行
cd frontend
npm install
npm run dev
```

本地运行后端时，`DB_HOST` 默认为 `localhost`，直连 Docker 暴露的 5432 端口。

## 数据库表结构

### users

| 列                 | 类型               | 说明              |
| ------------------ | ------------------ | ----------------- |
| id                 | SERIAL PK          | 自增主键          |
| student_id         | VARCHAR(50) UNIQUE | 学号，唯一        |
| name               | VARCHAR(100)       | 姓名              |
| phone / qq / email | VARCHAR            | 联系方式          |
| role               | VARCHAR(20)        | 角色，默认 'user' |
| created_at         | TIMESTAMP          | 创建时间          |

### lost_items（核心表）

| 列                      | 类型                   | 说明                       |
| ----------------------- | ---------------------- | -------------------------- |
| id                      | SERIAL PK              | 自增主键                   |
| item_name               | VARCHAR(200)           | 物品名称                   |
| item_type               | VARCHAR(50)            | 物品分类                   |
| description             | TEXT                   | 详细描述                   |
| location                | VARCHAR(200)           | 丢失/捡到地点              |
| lost_time / found_time  | TIMESTAMP              | 丢失/找到时间              |
| status                  | VARCHAR(20)            | 'lost' 或 'found'          |
| image_url               | VARCHAR(500)           | 物品图片路径               |
| contact_person/phone/qq | VARCHAR                | 联系人信息                 |
| **vector**        | **VECTOR(2048)** | **语义向量（核心）** |
| created_at / updated_at | TIMESTAMP              | 时间戳                     |

### match_records（计划用于智能匹配）

| 列                           | 类型             | 说明                                 |
| ---------------------------- | ---------------- | ------------------------------------ |
| id                           | SERIAL PK        | 自增主键                             |
| lost_item_id / match_item_id | FK → lost_items | 匹配对                               |
| similarity                   | FLOAT            | 余弦相似度                           |
| match_status                 | VARCHAR(20)      | 'pending' / 'confirmed' / 'rejected' |

pgvector 索引情况：`vector` 列 2048 维超过 pgvector 0.8.x 索引上限（2000 维），暂不建向量索引。校园级数据量（数千条）下暴力扫描完全够用。

## API 端点一览

### 用户管理

| 方法 | 路径                | 说明                 |
| ---- | ------------------- | -------------------- |
| GET  | `/api/users`      | 列出所有用户         |
| POST | `/api/users`      | 创建用户（学号唯一） |
| GET  | `/api/users/{id}` | 查询单个用户         |

### 失物管理

| 方法   | 路径                     | 说明                                   |
| ------ | ------------------------ | -------------------------------------- |
| GET    | `/api/lost-items`      | 分页列表（支持 status/item_type 筛选） |
| POST   | `/api/lost-items`      | 创建失物，自动生成向量                 |
| GET    | `/api/lost-items/{id}` | 查询单条                               |
| PUT    | `/api/lost-items/{id}` | 更新，名称/描述/图片变化时重新向量化   |
| DELETE | `/api/lost-items/{id}` | 删除                                   |

### 搜索

| 方法 | 路径                               | 说明                         |
| ---- | ---------------------------------- | ---------------------------- |
| GET  | `/api/search?query=xxx`          | 关键字搜索（ILIKE 模糊匹配） |
| GET  | `/api/semantic-search?query=xxx` | 语义搜索（向量余弦相似度）   |

### 统计

| 方法 | 路径           | 说明                   |
| ---- | -------------- | ---------------------- |
| GET  | `/api/stats` | 失物/招领/用户总数统计 |

## 核心流程：向量化管道

这是整个项目最关键的数据流，发生在创建和更新失物时：

```
POST /api/lost-items
  │
  │  { "item_name": "白色校园卡", "description": "...", "image_url": "..." }
  ▼
_build_vector(item_name, description, image_url)
  │
  │  拼接文本: "白色校园卡 ..."
  │
  ├── 有图片且文件存在？
  │   YES → encode_image(path)
  │           │ PIL.open → thumbnail(448,448) → model.encode()
  │   NO  → encode_text(text)
  │           │ model.encode(text, normalize_embeddings=True)
  │
  ▼
返回 float[] (长度 2048)，转为 pgvector 格式字符串 "[0.01,0.02,...]"
  │
  ▼
INSERT INTO lost_items (..., vector) VALUES (..., '[0.01,...]'::vector)
```

### 模型加载（embedding.py）

```python
# 服务启动时执行一次（FastAPI startup event）
init_model()
  │
  ├── 检测设备: MPS (Apple Silicon) > CUDA (NVIDIA) > CPU
  ├── 加载 Qwen/Qwen3-VL-Embedding-2B（约 4GB，2048 维输出）
  ├── local_files_only=True（离线使用，不从 HuggingFace 下载）
  └── 全局单例 _model，后续所有请求复用
```

设备行为：

- **Mac Apple Silicon**：float16 + MPS，单次编码 ~1s
- **Linux + NVIDIA GPU**：float16 + CUDA，单次编码 ~50ms
- **Docker / 无 GPU**：float32 + CPU，单次编码 ~2-5s

## 两种搜索的区别

### 关键字搜索（`/api/search`）

```sql
SELECT * FROM lost_items
WHERE item_name ILIKE '%关键词%'
   OR description ILIKE '%关键词%'
   OR location ILIKE '%关键词%'
ORDER BY created_at DESC
```

- 精确字符串匹配，用户输入什么就搜什么
- "无线耳机" 搜不到 "AirPods"

### 语义搜索（`/api/semantic-search`）

```sql
SELECT *, 1 - (vector <=> 查询向量::vector) AS similarity
FROM lost_items
WHERE vector IS NOT NULL
ORDER BY vector <=> 查询向量::vector
LIMIT 10
```

- `<=>` 是 pgvector 的余弦距离算子
- 查询文本先过 embedding 模型变成 2048 维向量
- "无线耳机" 能匹配到 "AirPods白色无线耳机"（实测相似度 0.74）
- "喝的" 能匹配到 "水杯"（实测相似度 0.55）
- 只返回有向量的物品（`WHERE vector IS NOT NULL`）

## 前端页面结构

```
App.vue (SPA 路由，currentPage 状态切换)
├── Header.vue          导航栏
├── HomePage.vue        首页（统计概览 + 快捷入口）
├── LostListPage.vue    失物列表（分页、筛选、搜索）
├── CreatePage.vue      发布失物/招领信息
└── AdminPage.vue       管理后台
```

前端通过 `axios` 调用后端 API（`baseURL: http://localhost:8000/api`）。在 Docker 环境下，浏览器访问 `localhost:5173` 加载前端页面，页面中的 JS 直接请求 `localhost:8000`（宿主机端口映射），无需 Vite 代理。

## QQ 机器人（计划中）

设计为 QQ 群内的失物查询入口，流程如下：

```
QQ 群消息 → NapCat (OneBot v11) → AstrBot → 调用 backend API
                                              │
                    ┌─────────────────────────┘
                    ▼
            /api/semantic-search?query=用户消息
                    │
                    ▼
            返回匹配结果，AstrBot 格式化回复到 QQ 群
```

`docker-compose.yml` 中已预留配置（默认注释），需要时取消注释并准备 NapCat 配置文件。

## 目录结构

```
find-my-bot/
├── docker-compose.yml       # 根编排文件
├── Dockerfile               # db 镜像（postgres:16 + pgvector）
├── .dockerignore
├── backend/
│   ├── Dockerfile           # 后端镜像
│   ├── entrypoint.sh        # 启动脚本（等 DB → 建表 → 启动）
│   ├── requirements.txt     # Python 依赖
│   ├── app.py               # FastAPI 主程序（所有端点）
│   ├── embedding.py         # 向量化模块（模型加载 + 编码）
│   └── schema.sql           # 数据库建表 DDL
├── frontend/
│   ├── Dockerfile           # 前端镜像（dev 模式）
│   ├── package.json         # Vue 3 + Element Plus + Vite
│   ├── vite.config.js
│   └── src/
│       ├── main.js          # 入口
│       ├── App.vue          # 根组件（页面路由）
│       ├── api/index.js     # axios API 封装
│       └── components/      # 页面组件
├── qqbot/
│   ├── docker-compose.yml   # QQ 机器人独立编排
│   ├── napcat/              # NapCat 配置（需自行准备）
│   └── astrbot/             # AstrBot 配置（需自行准备）
└── doc/
    ├── getting-started.md   # 从零开始启动教程
    ├── architecture.md      # 本文档
    └── related.md           # 参考链接
```
