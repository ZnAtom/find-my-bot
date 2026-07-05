# 校园失物招领 AI Agent - 服务启动指南

> 本文档说明如何启动所有服务，使 QQ 机器人接入大模型。

---

## 服务架构

```
QQ 用户 <---> NapCat (QQ协议) <---> AstrBot (机器人框架) <---> API 代理 <---> 学校 GenAI API
                                                         (端口8001)         (qwen-instruct)
```

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | 数据库 |
| 后端 FastAPI | 8000 | Web API |
| 前端 Vue 3 | 5173 | 管理后台 |
| NapCat | 3001, 6099 | QQ 协议（OneBot v11） |
| AstrBot | 6185, 6199 | 机器人框架 + WebSocket |
| API 代理 | 8001 | 转发请求到学校 API |

---

## 一键启动（推荐）

```bash
cd /home/zn/class/finging

# 1. 启动 API 代理
cd proxy && source ../backend/venv/bin/activate && python proxy.py > /tmp/proxy.log 2>&1 &
cd ..

# 2. 启动后端
cd backend && source venv/bin/activate && python app.py > /tmp/backend.log 2>&1 &
cd ..

# 3. 启动前端
cd frontend && npx vite --host 0.0.0.0 > /tmp/frontend.log 2>&1 &
cd ..

# 4. 确认 Docker 容器运行中
sudo docker start napcat astrbot
```

---

## 分步启动（详细）

### 第一步：启动 API 代理（必须先启动！）

代理负责将 AstrBot 的 OpenAI 格式请求转发到学校 GenAI API。

```bash
cd /home/zn/class/finging/proxy
source ../backend/venv/bin/activate
python proxy.py > /tmp/proxy.log 2>&1 &
```

验证代理是否正常：
```bash
curl -s http://localhost:8001/v1/models
# 应返回: {"object":"list","data":[{"id":"qwen-instruct",...}]}
```

### 第二步：启动 Docker 容器

```bash
# 启动 NapCat（QQ 协议）
sudo docker start napcat

# 启动 AstrBot（机器人框架）
sudo docker start astrbot
```

验证连接：
```bash
# 查看 NapCat 日志，确认 WebSocket 连接成功
sudo docker logs napcat 2>&1 | grep -i "websocket\|adapter" | tail -5

# 查看 AstrBot 日志，确认适配器已连接
sudo docker logs astrbot 2>&1 | grep -i "aiocqhttp\|adapter" | tail -5
```

### 第三步：启动后端和前端（可选，Web 管理后台用）

```bash
# 后端
cd /home/zn/class/finging/backend
source venv/bin/activate
python app.py > /tmp/backend.log 2>&1 &

# 前端
cd /home/zn/class/finging/frontend
npx vite --host 0.0.0.0 > /tmp/frontend.log 2>&1 &
```

---

## 首次部署 / 服务器重启后

### NapCat 需要重新扫码登录 QQ

```bash
# 查看二维码
sudo docker logs napcat 2>&1 | grep -A 20 "二维码"
```

或访问 WebUI：`http://localhost:6099/webui?token=94c9babc641f`

用手机 QQ 扫码登录后，NapCat 会自动连接 AstrBot。

### AstrBot 配置（首次需要）

1. 访问 `http://localhost:6185`
2. 登录（用户名 `astrbot`，密码在启动日志中）
3. 确认 **机器人** 页面有 OneBot v11 适配器，端口 `6199`
4. 确认 **服务提供商** 页面有 `qwen-instruct`，API 地址 `http://172.17.0.1:8001/v1`
5. 确认 **应用** 页面大模型已绑定到机器人

---

## 验证 QQ 机器人 + 大模型

1. 在 QQ 群中发送：`@find my 你好`
2. 等待几秒，机器人应回复大模型生成的内容
3. 如果报错，检查日志：

```bash
# 查看代理日志（确认请求到达）
cat /tmp/proxy.log | tail -20

# 查看 AstrBot 日志
sudo docker logs astrbot --tail 30

# 查看 NapCat 日志
sudo docker logs napcat --tail 20
```

---

## 停止服务

```bash
# 停止代理
pkill -f "python proxy.py"

# 停止后端
pkill -f "python app.py"

# 停止前端
pkill -f "vite"

# 停止 Docker 容器
sudo docker stop napcat astrbot
```

---

## 常见问题

### Q: QQ 机器人不回复消息
1. 确认 NapCat 已扫码登录：`sudo docker logs napcat | grep "二维码"`
2. 确认 NapCat 连接了 AstrBot：日志中应有 `WebSocket反向服务...已启动`
3. 确认 AstrBot 适配器已连接：日志中应有 `aiocqhttp(OneBot v11) 适配器已连接`
4. 确认代理在运行：`curl http://localhost:8001/v1/models`

### Q: 大模型返回 `EmptyModelOutputError`
- 代理必须运行，且 `model` 字段会被强制覆盖为 `qwen-instruct`
- 确认学校 API 可访问：`curl -s -X POST https://genaiapi.shanghaitech.edu.cn/api/v1/start -H "Authorization: Bearer YOUR_KEY" -H "Content-Type: application/json" -d '{"messages": [{"role": "user", "content": "你好"}]}'`

### Q: 代理启动失败
- 检查端口 8001 是否被占用：`lsof -i :8001`
- 检查虚拟环境：`cd /home/zn/class/finging/proxy && source ../backend/venv/bin/activate`

### Q: 服务器重启后服务没了
- Docker 容器设置了 `--restart=always`，会自动启动
- 代理和后端需要手动启动，或配置 systemd 服务

---

## 配置 systemd 自动启动（可选）

### API 代理

```bash
sudo tee /etc/systemd/system/findmy-proxy.service << 'EOF'
[Unit]
Description=FindMy API Proxy
After=network.target

[Service]
Type=simple
User=zn
WorkingDirectory=/home/zn/class/finging/proxy
ExecStart=/home/zn/class/finging/backend/venv/bin/python proxy.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable findmy-proxy
sudo systemctl start findmy-proxy
```

### 后端

```bash
sudo tee /etc/systemd/system/findmy-backend.service << 'EOF'
[Unit]
Description=FindMy Backend API
After=network.target

[Service]
Type=simple
User=zn
WorkingDirectory=/home/zn/class/finging/backend
ExecStart=/home/zn/class/finging/backend/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable findmy-backend
sudo systemctl start findmy-backend
```
