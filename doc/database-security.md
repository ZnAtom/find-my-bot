# 数据库安全运维

本文档分为本地运行和 K8s 生产运维两部分。当前本机调试使用本地 PostgreSQL；K8s CronJob 仍保留为生产部署方案。

## 本地运行注意事项

当前本地数据库监听在 `127.0.0.1:5432`，不应直接暴露到局域网或公网。局域网访问只通过 nginx 暴露 HTTP 80 端口，前端、后端和数据库都保持本机回环监听。

本地 `.env` 中的数据库密码、Casdoor secret、学校 GenAI API key 不应提交到 Git。排查问题时可以打印非敏感配置，例如端口、host、开关状态；不要在日志或文档中粘贴完整 key。

本地备份可以使用：

```bash
PGPASSWORD=password pg_dump -h 127.0.0.1 -p 5432 -U appuser -d lostfound \
  | gzip > lostfound-$(date +%Y%m%d-%H%M%S).sql.gz
```

备份文件可能包含联系方式、申请留言和通知内容，应放在非仓库目录，并设置为仅当前用户可读。

## 敏感联系方式清理

后端镜像内置 `cleanup_sensitive_data.py`。K8s 中的 `foundit-data-retention` CronJob 默认每天执行一次，清理 90 天前已完成或已过期记录中的联系方式。

清理范围：

- `lost_items.contact_person/contact_phone/contact_qq/contact_email/storage_location`
- `claim_requests.requester_name/requester_contact/message`
- `notifications.message`

手动试运行：

```bash
kubectl -n default create job --from=cronjob/foundit-data-retention foundit-data-retention-manual
kubectl -n default logs job/foundit-data-retention-manual
```

调整保留时间：

- 修改 `k8s/data-retention-cronjob.yaml` 里的 `CONTACT_RETENTION_DAYS`
- 默认值：`90`

## 加密备份

备份由 `foundit-db-backup` CronJob 执行：

- 每天导出 PostgreSQL
- 使用 gzip 压缩
- 使用 OpenSSL AES-256-CBC + PBKDF2 加密
- 写入 `foundit-db-backup-pvc`
- 默认保留 30 天

首次部署前创建备份加密密钥：

```bash
kubectl -n default create secret generic foundit-backup-secret \
  --from-literal=encryption_password='<一段足够长的随机备份密码>'
```

如果 Secret 已存在，更新方式：

```bash
kubectl -n default create secret generic foundit-backup-secret \
  --from-literal=encryption_password='<一段足够长的随机备份密码>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

手动触发一次备份：

```bash
kubectl -n default create job --from=cronjob/foundit-db-backup foundit-db-backup-manual
kubectl -n default logs job/foundit-db-backup-manual
```

查看备份文件：

```bash
kubectl -n default get pvc foundit-db-backup-pvc
kubectl -n default get jobs | grep foundit-db-backup
```

## 解密与恢复

解密示例：

```bash
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -pass env:BACKUP_ENCRYPTION_PASSWORD \
  -in lostfound-20260714T200000Z.sql.gz.enc \
  | gunzip > lostfound.sql
```

恢复示例：

```bash
PGPASSWORD='<数据库密码>' psql \
  -h '<数据库地址>' \
  -U appuser \
  -d lostfound \
  -f lostfound.sql
```

恢复前应先在临时数据库验证备份可用，不要直接覆盖生产库。

## 访问控制要求

- 不要把数据库 dump、解密后的 SQL、备份密码提交到 Git。
- `foundit-backup-secret` 只允许运维人员读取。
- `foundit-db-backup-pvc` 不挂载到业务 Pod，只由备份 CronJob 挂载。
- 从集群拷贝备份文件前，确认本地磁盘是加密磁盘，并设置文件权限为仅当前用户可读。
- 定期轮换 `foundit-backup-secret`，轮换后新备份使用新密码，旧备份仍需旧密码解密。

K8s 层面的访问控制：

- 所有业务 Pod 默认关闭 `automountServiceAccountToken`，避免容器被入侵后直接拿到 Kubernetes API token。
- `foundit-db-backup` 和 `foundit-data-retention` 使用专用 ServiceAccount，且不挂载 API token。
- `foundit-db-ingress` NetworkPolicy 只允许 `foundit-backend`、`foundit-db-backup`、`foundit-data-retention` 访问数据库 Pod 的 5432 端口。
- NetworkPolicy 是否生效取决于集群 CNI 是否支持并启用网络策略。

检查 NetworkPolicy 是否已下发：

```bash
kubectl -n default get networkpolicy foundit-db-ingress
kubectl -n default describe networkpolicy foundit-db-ingress
```
