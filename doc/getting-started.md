# 从零开始启动

## 环境要求

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose（Docker Desktop 自带）
- 如果不用 Docker，需要 Python 3.12+、Node.js 22+、PostgreSQL 16

## 1. 克隆项目

```bash
git clone <repo-url> find-my-bot
cd find-my-bot
```

## 2. 启动所有服务

```bash
docker compose up -d --build
```

首次构建会下载镜像并安装依赖，大约需要 3-5 分钟。

## 3. 验证服务

启动完成后三个容器都应该处于 `Up` 状态：

```bash
docker compose ps
```

预期输出：

```
NAME                 STATUS
findmybot-db         Up (healthy)
findmybot-backend    Up
findmybot-frontend   Up
```

### 测试后端 API

```bash
# 查看统计
curl http://localhost:8000/api/stats

# 创建一条失物信息
curl -X POST http://localhost:8000/api/lost-items \
  -H "Content-Type: application/json" \
  -d '{"item_name":"校园卡","description":"蓝色","location":"图书馆","contact_person":"张三"}'

# 搜索
curl "http://localhost:8000/api/search?query=校园卡"
```

### 访问前端

浏览器打开 http://localhost:5173

## 4. 服务端口一览

| 服务         | 地址                      | 说明                     |
| ------------ | ------------------------- | ------------------------ |
| 前端管理后台 | http://localhost:5173     | Vue 3 + Element Plus     |
| 后端 API     | http://localhost:8000/api | FastAPI，自动生成 /docs  |
| 数据库       | localhost:5432            | PostgreSQL 16 + pgvector |

## 5. 开发模式

源码通过 volume 挂载，修改代码后自动热重载：

- **前端**：编辑 `frontend/src/` 下的文件，浏览器即时刷新
- **后端**：编辑 `backend/app.py`，uvicorn 自动重启（`--reload`）
- **数据库**：修改 `backend/schema.sql` 后需要重启 backend 容器

```bash
docker compose restart backend
```

## 6. 常用命令

```bash
# 停止所有服务
docker compose down

# 停止并删除数据卷（数据库数据会丢失）
docker compose down -v

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs db

# 进入数据库
docker compose exec db psql -U appuser -d lostfound

# 重建单个服务
docker compose up -d --build backend
```

## 7. 数据库表结构

| 表                | 说明                                          |
| ----------------- | --------------------------------------------- |
| `users`         | 用户信息（学号、姓名、联系方式）              |
| `lost_items`    | 失物/招领信息，含 pgvector 向量列用于语义匹配 |
| `match_records` | 失物匹配记录（相似度打分）                    |

初始化 SQL 脚本：`backend/schema.sql`，容器首次启动时自动执行。

**首次启动说明**：后端首次启动时会自动从 HuggingFace 下载 Qwen 嵌入模型（约 4GB），需等待几分钟。国内网络可在 `docker-compose.yml` 中取消注释 `HF_ENDPOINT: https://hf-mirror.com` 使用镜像加速。如果模型已缓存在本地，设置 `HF_LOCAL_ONLY: "1"` 跳过下载。

## 8. QQ 机器人（可选）

根 `docker-compose.yml` 中已预留 napcat + astrbot 服务的配置（默认注释）。需要时取消注释并确保对应的配置文件已放置在 `qqbot/` 目录下。

## 9. 常见问题

### 端口冲突

如果本机已运行 PostgreSQL 或 8000/5173 端口被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "15432:5432"  # 将 5432 改为其他端口
```

同时修改 `docker-compose.yml` 中 backend 的 `DB_PORT` 环境变量。

### 构建失败

```bash
# 清理缓存后重试
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### 数据库数据持久化

数据库数据存储在 Docker 命名卷 `pgdata` 中。只要不执行 `docker compose down -v`，数据会一直保留。
