# FoundIt QQ 智能客服

当前版本把 QQ 私聊文本接入网站已有智能客服。知识库、物品搜索、模型调用、
脱敏规则和会话记录都由 FastAPI 后端统一处理；AstrBot 不连接数据库。群消息不会被
本插件处理，后续的群聊 keyword_gate 自动发布应作为独立流程实现。

## 1. 配置后端令牌

运行 openssl rand -hex 32 生成随机令牌。

本地开发时，把结果写入项目根目录未跟踪的 .env：

    QQ_BOT_SERVICE_TOKEN=生成的随机令牌

线上 K8s 使用 Secret，不要把令牌写进 YAML：

    kubectl create secret generic foundit-qq-bot \
      --from-literal=service_token='生成的随机令牌' \
      --dry-run=client -o yaml | kubectl apply -f -
    kubectl rollout restart deployment/foundit-backend

## 2. 启动 QQ 服务

    cd qqbot
    cp .env.example .env
    id -u
    id -g
    docker compose up -d
    docker compose logs -f napcat

首次登录时按 NapCat 日志或 http://127.0.0.1:6099/webui 的提示扫码。WebUI 只绑定
本机，不会直接暴露到局域网或公网。

首次扫码成功后，可以在 qqbot/.env 填写：

    NAPCAT_ACCOUNT=你的QQ号

之后容器启动会尝试快速登录该账号；如果 NapCat 提示登录态已失效，仍需要重新扫码。

## 3. 连接 NapCat 与 AstrBot

1. 打开 AstrBot：http://127.0.0.1:6185。
2. 在 AstrBot 中新增 OneBot v11/aiocqhttp 适配器，并让它监听容器内 6199 端口。
3. 在 NapCat WebUI 新增反向 WebSocket，地址填写 ws://astrbot:6199/ws。
4. 如果设置 OneBot access token，两端必须填写相同值。
5. 在 AstrBot 插件页重载“FoundIt 智能客服”。

不同 AstrBot/NapCat 版本的 WebUI 字段名称可能略有变化，以容器日志中的实际监听
地址为准。不要使用仓库里旧的 astrbot/config/astrbot.json 作为运行配置；当前
AstrBot 会把 WebUI 配置保存在已忽略的 qqbot/astrbot/data/。

## 4. 配置 FoundIt 插件

在 AstrBot 插件配置中填写：

- backend_base_url：当前本机部署使用 http://foundit.geekpie.club，经 nginx 转发到
  后端。只有当后端监听容器可访问的地址时，才使用内网后端地址。
- site_base_url：http://foundit.geekpie.club。
- service_token：与后端 QQ_BOT_SERVICE_TOKEN 完全相同。
- timeout_seconds：默认 90。
- batch_window_seconds：默认 5。同一用户连续发送的文字和图片会在最后一条消息后
  等待 5 秒，合并为一次上下文并只回复一次。

先在 QQ 私聊发送 /foundit_ping，应回复“FoundIt QQ 通道正常”；再发送“怎么发布
招领信息”验证网站客服链路。插件不会记录原始 QQ 号或消息正文，后端仅保存 HMAC
后的匿名会话归属以及网站客服原本就会保存的对话内容。

## 5. 私聊图片识别与搜索

私聊可以发送 1-3 张图片，也可以同时附带文字。后端会重新解码图片、清除 EXIF，
调用项目现有视觉模型提取物品名称、分类和描述，然后搜索进行中的公开物品。

QQ 把先发图片、再补充文字的操作拆成多个消息事件。插件按用户分别聚合这些事件，
默认在最后一条消息后静默 5 秒再处理，避免图片和说明被拆成两次问答。不同用户的
缓冲区完全隔离。

启用 EMBEDDING_ENABLED 且模型可用时，搜索会融合图片与文字联合向量；未启用时会
自动使用视觉识别结果进行文字检索。临时图片在单次请求结束后删除，不写入物品记录。
