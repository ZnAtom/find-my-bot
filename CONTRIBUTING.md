# 参与贡献 (Contributing)

感谢您对 FoundIt 项目的关注！我们欢迎任何人参与到开发中来。为了保证代码库的整洁和项目协作的高效，请在提交代码前仔细阅读以下指南。

## 1. 分支管理

本项目遵循标准的 GitHub Flow：
- **`main`**：生产环境的稳定代码分支，仅接收来自 `develop` 的 Pull Request。
- **`develop`**：开发主分支，所有日常的新功能和 Bug 修复合并至此分支。
- **`feature/*` 或 `fix/*`**：个人开发分支，请基于 `develop` 分支切出。

```bash
# 开发新功能前，切出个人分支
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

## 2. 提交规范 (Commit Message Guidelines)

请严格遵循 [Conventional Commits (约定式提交规范)](https://www.conventionalcommits.org/zh-hans/v1.0.0/)。自动构建流水线可能会依赖您的提交前缀。

常用的前缀有：
- `feat:` 新增功能 (Feature)
- `fix:` 修复 Bug
- `docs:` 修改文档
- `style:` 修改代码格式 (不影响代码运行的变动，如空格、缩进)
- `refactor:` 代码重构 (既不是新增功能，也不是修复 Bug)
- `perf:` 性能优化
- `test:` 增加测试
- `chore:` 构建过程或辅助工具的变动

示例：
```
feat: add global search functionality in header
fix: resolve 502 error during startup
```

## 3. 提交 PR (Pull Request)

1. 推送您的分支到 GitHub 仓库（如果您是外部协作者，请 Fork 仓库）。
2. 发起一个指向 `develop` 分支的 Pull Request。
3. 请尽可能详细地填写自动弹出的 PR 模板，说明您的变更动机、测试方法和截图。
4. 等待至少一位核心维护者 Review 后方可 Merge。

## 4. 本地开发环境设置

您可以选择 Docker 一键启动或本地裸机环境运行。详见 [doc/getting-started.md](doc/getting-started.md)。

## 5. 编码规范

- **Python (后端)**：推荐遵循 PEP 8 规范，使用 4 个空格缩进。建议使用 `black` 或 `ruff` 格式化代码。
- **Vue (前端)**：遵循 ESLint 和 Prettier 的默认推荐规则，2 个空格缩进。
- 请确保您的编辑器已安装并支持读取根目录的 `.editorconfig` 文件，它将帮您自动搞定基础的代码缩进问题。
