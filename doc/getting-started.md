# 从零开始启动

## 环境要求

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose（Docker Desktop 自带）
- Conda 环境（推荐）或 Python 3.12+

## 1. 克隆项目

```bash
git clone <repo-url> find-my-bot
cd find-my-bot
```

## 2. 启动 Docker 服务（数据库 + 前端）

```bash
docker compose up -d --build
```

首次构建会下载镜像并安装依赖。

## 3. 配置 Python 环境

```bash
# 创建并激活 conda 环境（推荐）
conda create -n findmybot python=3.12 -y
conda activate findmybot

# 安装后端依赖
pip install uvicorn fastapi psycopg2-binary pillow python-multipart
```

如果已有 hugging_face 环境，直接装依赖即可：

```bash
conda activate hugging_face
pip install uvicorn fastapi psycopg2-binary pillow python-multipart
```

> `sentence-transformers`、`torch` 等 AI 相关包如已在环境中则无需重复安装。

## 4. 启动后端

```bash
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

> **首次使用**：需要将 `embedding.py` 中的 `local_files_only` 改为 `False`（或将环境变量 `HF_LOCAL_ONLY` 设为 `"0"`），让模型从 HuggingFace 下载到本地缓存。下载完成后改回 `True`（或设置 `HF_LOCAL_ONLY=1`）即可跳过网络请求直接加载。

首次启动会自动下载 Qwen 嵌入模型（约 4GB）和 BGE 重排序模型（约 2.9GB），需等待几分钟。国内网络可设置 `HF_ENDPOINT=https://hf-mirror.com` 使用镜像加速。

## 5. 验证服务

启动完成后 Docker 容器应处于 `Up` 状态：

```bash
docker compose ps
```

预期输出：

```
NAME                  STATUS
findmybot-db          Up (healthy)
findmybot-frontend    Up
```

### 测试后端 API

```bash
# 查看统计
curl http://localhost:8000/api/stats

# 创建一条失物信息
curl -X POST http://localhost:8000/api/lost-items \
  -H "Content-Type: application/json" \
  -d '{"item_name":"校园卡","description":"蓝色","location":"图书馆","contact_person":"张三"}'

# 关键字搜索
curl "http://localhost:8000/api/search?query=校园卡"

# 语义搜索（含 BGE 重排序）
curl "http://localhost:8000/api/semantic-search?query=钱包&rerank=true"
```

### 访问前端

浏览器打开 http://localhost:5173

## 6. 服务端口一览

| 服务         | 地址                      | 说明                     |
| ------------ | ------------------------- | ------------------------ |
| 前端管理后台 | http://localhost:5173     | Vue 3 + Element Plus     |
| 后端 API     | http://localhost:8000/api | FastAPI，自动生成 /docs  |
| 数据库       | localhost:5432            | PostgreSQL 16 + pgvector |

## 7. 架构说明

```
Docker                      本地 (Conda)
┌─────────────┐            ┌─────────────────┐
│  db         │◄───────────│  uvicorn         │
│  PostgreSQL │   5432     │  FastAPI :8000   │
│  + pgvector │            │  + Qwen 嵌入模型  │
├─────────────┤            │  + BGE 重排序    │
│  frontend   │            └─────────────────┘
│  Vite :5173 │
└─────────────┘
```

- **数据库 + 前端** 由 Docker 托管
- **后端** 在本地 Conda 环境运行，利用 MPS/CUDA 加速 AI 推理

## 8. 开发模式

- **前端**：Docker 源码挂载，编辑 `frontend/src/` 即时热更新
- **后端**：`--reload` 自动监听文件变更重启
- **数据库**：修改 `backend/schema.sql` 后需手动重建表或重启 db 容器

```bash
docker compose restart db
```

## 9. 常用命令

```bash
# 停止 Docker 服务
docker compose down

# 停止并删除数据卷（数据库数据会丢失）
docker compose down -v

# 查看日志
docker compose logs -f frontend
docker compose logs db

# 进入数据库
docker compose exec db psql -U appuser -d lostfound

# 重建 Docker 服务
docker compose up -d --build
```

## 10. 数据库表结构

| 表              | 说明                                          |
| --------------- | --------------------------------------------- |
| `users`         | 用户信息（学号、姓名、联系方式）              |
| `lost_items`    | 失物/招领信息，含 pgvector 向量列用于语义匹配 |
| `match_records` | 失物匹配记录（相似度打分）                    |

初始化 SQL 脚本：`backend/schema.sql`，数据库容器首次启动时自动执行。

## 11. QQ 机器人（可选）

根 `docker-compose.yml` 中已预留 napcat + astrbot 服务的配置（默认注释）。需要时取消注释并确保对应的配置文件已放置在 `qqbot/` 目录下。

## 12. 常见问题

### 端口冲突

如果本机已运行 PostgreSQL 或 8000/5173 端口被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "15432:5432"  # 将 5432 改为其他端口
```

### 构建失败

```bash
# 清理缓存后重试
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### 数据库数据持久化

数据库数据存储在 Docker 命名卷 `pgdata` 中。只要不执行 `docker compose down -v`，数据会一直保留。

### 模型下载慢 / 网络不通

设置 HuggingFace 镜像：

```bash
HF_ENDPOINT=https://hf-mirror.com python -m uvicorn app:app ...
```

模型下载完成后，后续可用 `HF_LOCAL_ONLY=1` 跳过网络请求直接加载本地缓存。

## 13. K8s 部署与常见排错 (Kubernetes / GitOps)

如果您正在使用 ArgoCD 或 Kubernetes 将应用部署到云端集群，请注意以下常见陷阱及解决方案：

### 13.1. Nginx 返回 502 Bad Gateway
**原因**：后端容器在启动时需要下载大语言模型（如 Qwen3 2B，约 2GB），下载过程可能会持续数分钟。如果 K8s 没配置就绪探针（readinessProbe），Nginx Ingress 会在模型下载期间就将用户请求转发过去，由于 FastAPI 还没监听端口，所以直接返回 502。
**解决**：在后端的 `Deployment` 配置文件中配置 `readinessProbe`，例如：
```yaml
readinessProbe:
  httpGet:
    path: /docs
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
```

### 13.2. 部署到云端后，打开前端页面报 403 Forbidden
**原因**：Vite 5 默认具有严格的 Host 头校验。如果您通过自己的域名（而不是 localhost）访问 Vite 开发服务器（`npm run dev`），Vite 会为了防御 DNS 重绑定攻击直接拦截请求。
**解决**：在前端的 `vite.config.js` 中配置 `server: { allowedHosts: true }`，或者将您的正式域名加入 allowedHosts 列表。

### 13.3. 后端 Pod 不断重启 (CrashLoopBackOff)
**原因**：如果您使用的是海外的模型源（如 HuggingFace），在国内 K8s 节点上极大概率会触发 `Connection reset by peer` 错误，导致容器崩溃并无限重启。或者 `DB_PASSWORD` 等关键连接环境变量缺失。
**解决**：
1. 检查环境变量中是否带全了所有数据库信息（`DB_USER`、`DB_PASSWORD`、`DB_HOST`、`DB_NAME`）。
2. 在后端的 Kubernetes 环境变量 (env) 中强制注入国内镜像：
```yaml
- name: HF_ENDPOINT
  value: "https://hf-mirror.com"
```

### 13.4. Ingress HTTPS 证书报错 (ERR_SSL_PROTOCOL_ERROR)
**原因**：通常是因为集群外部还有一层代理服务器（例如校园网的 Caddy/FRP 网关）。如果在您的 DNS 解析链路中，外部网关尝试接管 HTTPS 但又没有配置对应的证书，就会导致握手失败。
**解决**：
- 确保 CNAME 解析到了正确的入口 IP。如果是校园网，可以尝试直连 K8s 节点的内部域名。
- 如果需要 K8s 自己签发证书，可以在 Ingress 的 annotations 中加上 `cert-manager.io/cluster-issuer: letsencrypt-prod-dns` 来使用 Cert-Manager 的 DNS 验证自动下发证书。
