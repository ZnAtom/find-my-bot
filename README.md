# FoundIt (原 find-my-bot)

校园统一失物招领 AI Agent。

## 部署与启动指南

本作支持两种部署方式：
- **Docker 一键启动**：适合本地开发或无 K8s 环境的协作者，教程见 [doc/getting-started.md](doc/getting-started.md)。
- **Kubernetes (K8s) 全自动 GitOps 部署**：适合生产环境，只需 `git push` 即可通过 GitHub Actions 与 ArgoCD 全自动部署。详见 [doc/getting-started.md](doc/getting-started.md) 中的 Kubernetes 章节。

关于项目架构详情，请参考 [doc/architecture.md](doc/architecture.md)。
