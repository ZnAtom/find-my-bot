# 本地启动指南

本文档描述通用 Linux 本地运行方式。推荐模式是：Docker Compose 启动 PostgreSQL，FastAPI 和 Vite 直接跑在宿主机，必要时用 nginx 暴露到局域网 80 端口。当前服务器的域名/IP 细节放在 [server-local.md](server-local.md)，不要把那里的值当成其他设备的默认配置。

## 1. 环境要求

基础依赖：

- Ubuntu 22.04 或同类 Linux
- Python 3.10+，推荐 3.12
- Node.js 22+ 和 npm
- Docker + Docker Compose，用于默认数据库
- `psql`
- 可选：PostgreSQL + pgvector，如果不想用 Docker 数据库
- 可选：nginx，用于局域网或域名无端口访问
- 可选：`gettext-base`，用于提供 `envsubst` 生成 nginx 本地配置

embedding 依赖由脚本安装到 `backend/.venv`：

- `torch`
- `sentence-transformers`
- `rank-bm25`
- `jieba`

默认相对 embedding 模型路径：

```text
model/models--Qwen--Qwen3-VL-Embedding-2B
```

## 2. `.env` 关键配置

首次运行时可从 `.env.example` 复制：

```bash
cp .env.example .env
```

通用本地配置形态：

```text
DB_MODE=docker
DB_HOST=127.0.0.1
DB_PORT=5433
DB_USER=appuser
DB_PASSWORD=password
DB_NAME=lostfound

BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=5173

EMBEDDING_ENABLED=0
INSTALL_EMBEDDING_DEPS=0
HF_LOCAL_ONLY=1
EMBEDDING_MODEL_PATH=model/models--Qwen--Qwen3-VL-Embedding-2B
VECTOR_DIM=1536

SUPPORT_AUTO_IMPORT=1
SUPPORT_DOCS_DIR=doc/support
```

如果当前设备已经安装 pgvector、已放置模型，并希望搜索和客服一启动就使用 embedding，再把下面两项改成 `1`：

```text
INSTALL_EMBEDDING_DEPS=1
EMBEDDING_ENABLED=1
```

图像识别和客服 LLM 依赖学校 GenAI API：

```text
SCHOOL_API_URL=https://genaiapi.shanghaitech.edu.cn/api/v1/start
SCHOOL_API_KEY=<不要提交到 Git>
SCHOOL_VISION_MODEL=GPT-5.5
SUPPORT_LLM_MODEL=GPT-5.5
```

Casdoor 登录需要保持回调地址和访问入口一致。例如局域网域名入口：

```text
FRONTEND_BASE_URL=http://your-host.example
CASDOOR_REDIRECT_URI=http://your-host.example/api/auth/callback
CORS_ORIGINS=http://your-host.example,http://your-lan-ip
CSRF_TRUSTED_ORIGINS=http://your-host.example,http://your-lan-ip
```

## 3. 首次安装依赖

```bash
cd find-my-bot
bash dev-local.sh setup
```

脚本会：

1. 创建或复用 `backend/.venv`。
2. 安装后端 Python 依赖。
3. 在 `INSTALL_EMBEDDING_DEPS=1` 时安装 embedding 相关依赖。
4. 安装前端 npm 依赖。

如果本地没有模型且允许联网下载，可以临时设置：

```bash
HF_LOCAL_ONLY=0 bash dev-local.sh setup
```

下载完成后建议恢复 `HF_LOCAL_ONLY=1`，让服务只从本地模型目录加载。

## 4. 数据库准备

默认脚本使用 Docker Compose 的 `db` 服务。如果要改用宿主机 PostgreSQL：

```bash
sudo apt-get install postgresql postgresql-contrib
```

数据库至少需要：

```sql
CREATE USER appuser WITH PASSWORD 'password';
CREATE DATABASE lostfound OWNER appuser;
```

pgvector 推荐安装并启用。如果系统源有对应包，可以直接安装 PostgreSQL 版本匹配的 pgvector 包。如果没有包，可从源码构建。下面示例以 PostgreSQL 14 为例，其他版本需要替换 `postgresql-server-dev-14`：

```bash
sudo apt-get install build-essential postgresql-server-dev-14
git clone --branch v0.8.5 https://github.com/pgvector/pgvector.git /tmp/pgvector
cd /tmp/pgvector
make
sudo make install
```

启用扩展：

```bash
sudo -u postgres psql -d lostfound -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

检查：

```bash
PGPASSWORD=password psql -h 127.0.0.1 -p 5432 -U appuser -d lostfound \
  -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
```

启动脚本会执行 `backend/schema.sql`。如果 pgvector 可用，会自动创建：

```sql
lost_items.vector VECTOR(1536)
```

并创建 HNSW 索引：

```sql
idx_lost_items_vector
```

如果 pgvector 不可用，schema 会跳过向量列，搜索和客服会退回 BM25 词法能力。

## 5. 启动服务

```bash
bash dev-local.sh start
```

重启：

```bash
bash dev-local.sh restart
```

查看状态：

```bash
bash dev-local.sh status
```

正常状态类似：

```text
[db] ok (docker 127.0.0.1:5433/lostfound)
[backend] ok pid=... :8000
[frontend] ok pid=... :5173
```

`start/restart/db` 会自动同步客服知识库：

```text
doc/support/*.md -> support_knowledge_sources / support_knowledge_chunks
```

需要强制重导入时：

```bash
bash dev-local.sh support-import
```

## 6. 访问地址

本机直接访问：

```text
http://127.0.0.1:5173/
```

配置 nginx 后，局域网设备访问：

```text
http://your-lan-ip/
```

配置 DNS 或 hosts 后，域名访问：

```text
http://your-host.example/
```

注意：

- 没有配置 HTTPS 时，`https://...` 会拒绝连接，浏览器必须使用 `http://`。
- 域名如果解析到内网 IP，只能同局域网、校园网或 VPN 内访问。
- 如果 IP 能访问但域名拒绝，通常是客户端 DNS、代理规则或浏览器自动升级 HTTPS 的问题。

## 7. nginx 配置

项目内只提交模板：

```text
deploy/nginx/foundit-local.conf.template
```

按当前设备生成本地配置：

```bash
SERVER_NAMES="localhost 127.0.0.1" \
BACKEND_UPSTREAM="127.0.0.1:8000" \
FRONTEND_UPSTREAM="127.0.0.1:5173" \
envsubst '$SERVER_NAMES $BACKEND_UPSTREAM $FRONTEND_UPSTREAM' \
  < deploy/nginx/foundit-local.conf.template \
  > deploy/nginx/foundit-local.conf
```

安装到系统 nginx：

```bash
sudo install -m 0644 deploy/nginx/foundit-local.conf /etc/nginx/sites-available/foundit-local.conf
sudo ln -sf /etc/nginx/sites-available/foundit-local.conf /etc/nginx/sites-enabled/foundit-local.conf
sudo nginx -t
sudo systemctl restart nginx
```

配置会把：

```text
/api/*      -> 127.0.0.1:8000
/uploads/*  -> 127.0.0.1:8000
其他路径     -> 127.0.0.1:5173
```

## 8. 常用验证命令

前端：

```bash
curl -sS -o /tmp/index.html -w "%{http_code}" http://127.0.0.1:5173/
```

后端未登录状态：

```bash
curl -sS -o /tmp/me.json -w "%{http_code}" http://127.0.0.1:5173/api/auth/me
```

预期是 `401`，表示 API 可达但未登录。

语义搜索：

```bash
curl "http://127.0.0.1:8000/api/semantic-search?query=学生证&limit=5"
```

客服：

```bash
curl -sS \
  -H "Origin: http://localhost:5173" \
  -H "Content-Type: application/json" \
  -d '{"message":"我丢了一个学生证，请帮我寻找","channel":"web"}' \
  http://127.0.0.1:8000/api/support/chat
```

## 9. 测试

后端测试：

```bash
backend/.venv/bin/python -m pytest -q backend/tests/test_retrieval.py backend/tests/test_support.py
```

前端测试和构建：

```bash
cd frontend
npm test
npm run build
```

## 10. Docker 模式

Docker 编排仍保留：

```bash
docker compose up -d --build
```

当前配置特点：

- db 暴露到 `127.0.0.1:5433`。
- backend 暴露到 `127.0.0.1:8000`。
- frontend 暴露到 `127.0.0.1:5173`。
- backend 挂载 `./doc` 和 `./model`。
- `EMBEDDING_ENABLED` 默认可通过环境变量控制，Docker 内 CPU 推理会比较慢。

如果 Docker Hub 拉镜像超时，可以优先使用当前本地运行方式。

## 11. 常见问题

### 客服匿名发送返回 403

检查访问地址是否在：

```text
CSRF_TRUSTED_ORIGINS
CORS_ORIGINS
```

通过 nginx 无端口访问时，origin 是 `http://your-host.example` 或 `http://your-lan-ip`，不是旧的 `:5173` 地址。

### 登录提示 Redirect URI 不允许

Casdoor 后台需要加入当前回调地址，例如：

```text
http://your-host.example/api/auth/callback
```

### 客服或搜索没有使用 embedding

确认：

```text
EMBEDDING_ENABLED=1
HF_LOCAL_ONLY=1
EMBEDDING_MODEL_PATH=...
```

并确认数据库有 pgvector：

```sql
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

### 修改 `doc/support/*.md` 后是否要手动导入

通常不需要。`SUPPORT_AUTO_IMPORT=1` 时，`dev-local.sh start/restart/db` 会自动同步。只有需要立即强制刷新时才运行：

```bash
bash dev-local.sh support-import
```

### 看日志

```bash
bash dev-local.sh logs
tail -f .local/logs/backend.log
tail -f .local/logs/frontend.log
```
