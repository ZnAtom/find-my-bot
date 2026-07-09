<div align="center">
  <h1>🔍 FoundIt (原 find-my-bot)</h1>
  <p><strong>校园统一失物招领 AI Agent</strong></p>

  <!-- 徽章区域 -->
  <p>
    <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License">
    <img src="https://img.shields.io/badge/Vue-3.x-4FC08D?logo=vuedotjs" alt="Vue 3">
    <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/PostgreSQL-16.x-336791?logo=postgresql" alt="PostgreSQL">
  </p>
</div>

---

## 🌟 简介

**FoundIt** 是一个基于人工智能驱动的校园级失物招领解决方案。
它将计算机视觉与自然语言处理模型深度集成，通过将失物信息和招领信息转化为高维语义向量，实现超越传统字面关键字匹配的**语义级搜索**。
不论你是想找回遗失的“白色 Airpods”，还是登记捡到的“苹果无线耳机”，FoundIt 都能在瞬间智能匹配它们。

## ✨ 核心特性

- 🧠 **AI 语义搜索**：采用 `Qwen3-VL-Embedding-2B` 模型计算向量，利用 `pgvector` 在数据库层实现毫秒级余弦相似度匹配。
- 🖼️ **多模态支持**：文本描述与物品图片皆可转化为高维向量。
- ⚡ **现代化技术栈**：前后端分离架构，极致性能。
- 🤖 **QQ 机器人集成**：支持通过 NapCat + AstrBot 在群聊中无缝接入查询（开发中）。
- 🚀 **云原生就绪**：提供一键式 Docker 部署，以及针对 Kubernetes 的全自动 GitOps (ArgoCD) 流水线。

## 🛠️ 技术栈

- **前端 (Frontend)**: Vue 3, Vite, Element Plus
- **后端 (Backend)**: FastAPI, Python 3.12, Sentence Transformers, Uvicorn
- **数据库 (Database)**: PostgreSQL 16 + pgvector (向量扩展)
- **部署 (Deployment)**: Docker / Docker Compose / Kubernetes (ArgoCD)

## 🚀 部署与快速开始

本作支持多种部署方式，满足不同规模与场景的需求：

- **📦 Docker 一键启动**：适合本地开发、评估或无 K8s 环境的协作者，详细教程请参考 [👉 Docker 部署指南](doc/getting-started.md)。
- **☁️ Kubernetes 生产级 GitOps**：适合大型生产环境，无需人工干预即可在每次 Push 后自动构建并零停机滚动更新集群。配置说明见 [👉 K8s 部署指南](doc/getting-started.md#13-kubernetes-k8s-生产部署全自动-gitops)。

关于系统更深层次的架构设计、数据流向以及模型推理策略，请阅读 [👉 架构设计文档](doc/architecture.md)。

## 🤝 参与贡献

我们非常欢迎来自社区的反馈和贡献！在提交代码前，请务必阅读我们的 [贡献指南 (CONTRIBUTING.md)](CONTRIBUTING.md)。

- 发现 Bug 或有绝妙的新功能点子？请提交 [Issue](https://github.com/ZnAtom/find-my-bot/issues/new/choose)。
- 请遵守我们的 [社区行为准则 (CODE_OF_CONDUCT.md)](CODE_OF_CONDUCT.md)。

## 📄 协议

本项目基于 **MIT License** 开源。详情请参阅 [LICENSE](LICENSE) 文件。
