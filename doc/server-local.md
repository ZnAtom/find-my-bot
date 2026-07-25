# 当前服务器本地部署记录

本文记录当前这台 Ubuntu 服务器的局域网部署形态，只作为本机运维参考。其他设备部署时请优先看 [getting-started.md](getting-started.md)，不要直接复用这里的 IP、域名或 Casdoor 回调地址。

## 入口

```text
http://10.15.28.8/
http://foundit.geekpie.club/
```

`foundit.geekpie.club` 当前解析到内网 IP `10.15.28.8`。公网设备无法直接访问，必须处于同局域网、校园网或 VPN 环境。

当前未配置 HTTPS：

```text
https://foundit.geekpie.club/
```

会拒绝连接或被浏览器自动升级导致访问失败。

## 服务拓扑

```text
nginx :80
  /api/*      -> FastAPI 127.0.0.1:8000
  /uploads/*  -> FastAPI 127.0.0.1:8000
  其他路径     -> Vite 127.0.0.1:5173

PostgreSQL
  127.0.0.1:5432/lostfound
```

当前 `.env` 使用宿主机 PostgreSQL：

```text
DB_MODE=local
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=appuser
DB_NAME=lostfound
```

## 模型和知识库

本服务器把 Qwen embedding 模型放在项目目录内：

```text
model/models--Qwen--Qwen3-VL-Embedding-2B
```

推荐 `.env` 使用相对路径：

```text
INSTALL_EMBEDDING_DEPS=1
EMBEDDING_ENABLED=1
HF_LOCAL_ONLY=1
EMBEDDING_MODEL_PATH=model/models--Qwen--Qwen3-VL-Embedding-2B
SUPPORT_DOCS_DIR=doc/support
SUPPORT_AUTO_IMPORT=1
```

`dev-local.sh start/restart/db` 会自动同步 `doc/support/*.md` 到客服知识库。需要强制刷新时运行：

```bash
bash dev-local.sh support-import
```

## Casdoor

本服务器通过 nginx 同域反代，Casdoor 后台需要允许：

```text
http://foundit.geekpie.club/api/auth/callback
```

`.env` 中相关来源需要包含：

```text
FRONTEND_BASE_URL=http://foundit.geekpie.club
CASDOOR_REDIRECT_URI=http://foundit.geekpie.club/api/auth/callback
CORS_ORIGINS=http://foundit.geekpie.club,http://10.15.28.8
CSRF_TRUSTED_ORIGINS=http://foundit.geekpie.club,http://10.15.28.8
```

## nginx 配置

仓库只提交模板 `deploy/nginx/foundit-local.conf.template`。本服务器可以这样生成本地配置：

```bash
SERVER_NAMES="foundit.geekpie.club 10.15.28.8" \
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
