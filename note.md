# 项目部署经验记录

> 本文档记录校园统一失物招领 AI Agent 项目部署过程中的成功经验和失败教训，避免重复踩坑。

---

## 一、环境信息

- 系统：Ubuntu 24.04 LTS
- Docker：已安装
- 项目目录：`/home/zn/class/finging/`
- QQ 号：3617294080
- 学校 GenAI API：`https://genaiapi.shanghaitech.edu.cn/api/v1/start`
- 模型：`qwen-instruct`

---

## 二、各模块部署经验

### 2.1 Docker 安装与配置

**失败经验：**
- Docker Hub 国内拉取镜像慢/失败
- `ankane/pgvector` 镜像不存在

**成功经验：**
- 配置 Docker 镜像源：`/etc/docker/daemon.json` 添加 `https://docker.m.daocloud.io`
- pgvector 改为在 PostgreSQL 16 容器中从源码编译
- NapCat 使用代理镜像源 `docker.1ms.run` 拉取

---

### 2.2 前端 Vue 3 + Element Plus

**失败经验：**
- `@element-plus/icons-vue` 图标名称猜错，导致 `does not provide an export named 'X'` 错误

| 错误名称 | 正确名称 |
|---------|---------|
| `CheckCircle` | `CircleCheck` |
| `Image` | `Picture` |
| `Package` | `Box` |
| `Search`（未使用需删除导入） | - |

**成功经验：**
- 遇到图标导出错误时，先用 `grep "default as" node_modules/@element-plus/icons-vue/dist/index.js` 查正确名称
- 不要猜测图标名，必须查源码确认

---

### 2.3 NapCat (OneBot v11) 部署

**失败经验：**
- GitHub 仓库地址错误（`NapNeko/NapCat`、`NapCatQQ/NapCat` 都不对）
- Docker 镜像拉取卡住/超时
- 安装脚本需要 root 权限（`sudo`）
- WebSocket 连接 AstrBot 时 401 错误：
  - 原因1：NapCat 配置中 `websocketClients` 为空，未配置连接 AstrBot
  - 原因2：AstrBot 设置了 `ws_reverse_token`，但 NapCat 没带 token
  - 原因3：token 传递方式不对（URL query param vs header）

**成功经验：**
- 使用官方安装脚本：`curl -o napcat.sh https://nclatest.znin.net/NapNeko/NapCat-Installer/main/script/install.sh`
- Docker 部署命令：
  ```bash
  sudo docker run -d -e ACCOUNT=QQ号 -e WS_ENABLE=true \
    -e NAPCAT_GID=0 -e NAPCAT_UID=0 \
    -p 3001:3001 -p 6099:6099 \
    --name napcat --restart=always \
    docker.1ms.run/mlikiowa/napcat-docker:latest
  ```
- NapCat 配置文件路径：`/app/napcat/config/onebot11_QQ号.json`
- 最终解决方案：清空 AstrBot 的 `ws_reverse_token`（设为空字符串），NapCat 无需 token 即可连接
- NapCat 重启后登录态会失效，需要重新扫码

---

### 2.4 AstrBot 部署

**失败经验：**
- `provider` 配置格式错误，反复报 `KeyError: 'enable'`、`KeyError: 'type'`、`Missing credentials`
- 直接填 `key` 和 `api_base` 到 `provider` 中无效
- 学校 API 不是标准 OpenAI 格式（端点是 `/api/v1/start` 而非 `/v1/chat/completions`）
- 学校 API 返回 `tool_calls: []` 字段，导致 AstrBot 的 OpenAI SDK 解析失败（`EmptyModelOutputError`）

**成功经验：**
- Docker 部署：
  ```bash
  sudo docker run -d --name astrbot --restart=always \
    -p 6185:6185 -p 6199:6199 -e TZ=Asia/Shanghai \
    soulter/astrbot:latest
  ```
- AstrBot 默认登录：用户名 `astrbot`，密码在启动日志中
- **provider 正确配置方式**：`provider` 通过 `provider_source_id` 关联 `provider_sources`，而不是自己包含 key
  ```json
  "provider": [{
    "id": "qwen-instruct",
    "models": ["qwen-instruct"],
    "enable": true,
    "type": "openai_chat_completion",
    "provider_source_id": "qwen-instruct"
  }],
  "provider_sources": [{
    "provider": "openai",
    "type": "openai_chat_completion",
    "provider_type": "chat_completion",
    "key": ["API_KEY"],
    "api_base": "http://172.17.0.1:8001/v1",
    "timeout": 120,
    "id": "qwen-instruct",
    "enable": true
  }],
  "provider_settings": {
    "default_provider_id": "qwen-instruct"
  }
  ```
- **NapCat 连接 AstrBot**：在 NapCat 配置中添加：
  ```json
  "websocketClients": [{
    "enable": true,
    "url": "ws://172.17.0.1:6199/ws",
    "messagePostFormat": "array",
    "reportSelfMessage": false,
    "reconnectInterval": 1000,
    "accessToken": ""
  }]
  ```
  （`172.17.0.1` 是 Docker 宿主机地址）

---

### 2.5 API 代理（关键！）

**背景：** 学校 GenAI API 端点是 `/api/v1/start`，不是标准 OpenAI 的 `/v1/chat/completions`。AstrBot 的 OpenAI 适配器会自动拼接路径，所以需要一个代理做路径映射。

**失败经验：**
- 直接用学校 API 地址配置 AstrBot 会 404/500
- 学校 API 返回 `tool_calls: []` 字段，AstrBot 的 OpenAI SDK 解析后 `choices=None`，报 `EmptyModelOutputError`
- AstrBot 发送的请求包含 `tools`、`tool_choice` 等学校 API 不支持的字段
- **AstrBot 发送的 `model` 字段值是 `unknown`**，学校 API 返回 `The model 'unknown' does not exist`（404）
- 流式响应时 `resp.text` 已被消费导致 `StreamConsumed` 错误

**成功经验：**
- 代理文件：`/home/zn/class/finging/proxy/proxy.py`
- 代理端口：8001
- 代理功能：
  1. 将 `/v1/chat/completions` 请求转发到学校 API `/api/v1/start`
  2. **强制覆盖 `model` 字段为 `qwen-instruct`**（AstrBot 发送的 model 是 `unknown`）
  3. 过滤请求中不支持的字段：`tools`、`tool_choice`、`response_format`、`parallel_tool_calls`、`function_call`
  4. 过滤消息中 message 级别的 `tool_calls` 和 `tool_call_id`
  5. 清理响应中的 `tool_calls` 字段（避免 AstrBot SDK 解析失败）
  6. 提供 `/v1/models` 端点返回模型列表
  7. 流式错误时用 `resp.aread()` 代替 `resp.text` 避免 StreamConsumed
- 启动命令：
  ```bash
  cd /home/zn/class/finging/proxy && source ../backend/venv/bin/activate && python proxy.py > /tmp/proxy.log 2>&1 &
  ```
- **注意：服务器重启后需要重新启动代理！**

**学校 API 文档要点（来自 api.md）：**
- 端点：`https://genaiapi.shanghaitech.edu.cn/api/v1/start`（完整路径，不是 base URL）
- 认证：`Authorization: Bearer YOUR_API_KEY`
- 请求体：`{"stream": false, "messages": [...]}`（基础示例中没有 `model` 字段）
- 仅支持校内网络访问
- 模型 ID：`qwen-instruct`（对应 Qwen3.5-397B-A17B）

---

### 2.6 Git 仓库管理

**成功经验：**
- `.gitignore` 排除：`venv/`、`node_modules/`、Docker 数据目录、`.log`、`.env`
- 仓库地址：`git@github.com:ZnAtom/find-my-bot.git`
- 分支：`main`

---

## 三、当前服务状态

| 服务 | 端口 | 状态 |
|------|------|------|
| PostgreSQL + pgvector | 5432 | 运行中 |
| 后端 FastAPI | 8000 | 运行中 |
| 前端 Vue 3 | 5173 | 运行中 |
| NapCat (QQ协议) | 3001, 6099 | 运行中 |
| AstrBot (机器人框架) | 6185, 6199 | 运行中 |
| API 代理 | 8001 | 运行中 |

---

## 四、待完成

- [x] 验证 QQ 机器人 + 大模型完整流程（代理已修复 model=unknown 问题，测试通过）
- [ ] 前端搜索功能实现
- [ ] 图片上传功能
- [ ] 用户认证系统
- [ ] 向量搜索（pgvector 实际接入）
- [ ] 服务器持久化部署（systemd 服务 / docker-compose 统一管理）
- [ ] 迁移到服务器（需确认服务器在校园网内，否则学校 API 无法访问）

---

## 五、常用命令速查

```bash
# 查看服务日志
sudo docker logs napcat --tail 20
sudo docker logs astrbot --tail 20
cat /tmp/proxy.log

# 重启服务
sudo docker restart napcat
sudo docker restart astrbot

# 重启代理
pkill -f "python proxy.py"
cd /home/zn/class/finging/proxy && source ../backend/venv/bin/activate && python proxy.py > /tmp/proxy.log 2>&1 &

# 测试代理
curl -s http://localhost:8001/v1/models
curl -s -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-instruct", "messages": [{"role": "user", "content": "你好"}]}'

# 查看 NapCat 二维码
sudo docker logs napcat 2>&1 | grep -A 20 "二维码"
```
