# zero-rss 🚀

**私有化 RSS 订阅系统** — 用户自定义 Python 脚本，按需生成/更新 RSS 订阅源。

## ✨ 特性

- 📦 **Docker Compose 一键部署**，前后端分离
- 🐍 **Python 用户脚本**，自由定制数据抓取逻辑
- 🔧 **脚本参数系统**，同一脚本不同参数 = 多个独立 RSS 源
- ⏰ **四种触发方式**：间隔触发、定时触发（多时间点）、刷新触发、手动触发
- 📡 **标准 RSS 2.0** 输出，兼容所有 RSS 阅读器
- 🔒 Token 认证，安全可控
- 🎨 美观的 Web 管理界面 (Naive UI)

## 📌 版本

- 当前版本：`1.1.0`
- 版本源文件：`VERSION`

## 🐳 Docker 镜像自动发布

项目内置 GitHub Actions 工作流，可自动构建并推送后端/前端镜像到 Docker Hub。

需要在仓库 `Settings -> Secrets and variables -> Actions` 配置：

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`（建议使用 Docker Hub Access Token）

工作流文件：`.github/workflows/docker-publish.yml`

触发方式：

- push 到 `main`
- push tag（如 `v1.1.0`）
- 手动触发（`workflow_dispatch`）

标签策略：

- `latest` 仅在 push `v*` 版本标签时更新
- `main` 分支推送只会更新分支/sha 相关标签，不覆盖 `latest`

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose

### 一键部署

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd zero-rss

# 2. 配置环境变量 (修改 AUTH_TOKEN)
cp .env.example .env
# 编辑 .env，将 AUTH_TOKEN 改为你的安全令牌

# 3. 启动
docker compose up -d

# 4. 访问
# 前端: http://localhost:11081
# API:  http://localhost:11080/docs
```

### 开发模式

```bash
# 后端
cd backend
python -m uvicorn src.main:app --reload --port 11080

# 前端
cd frontend
npm install
npm run dev
```

## 📖 用户指南

### 概念

| 概念 | 说明 |
|------|------|
| **脚本模板** | 一个 `.py` 文件，包含元数据和 `run()` 函数 |
| **脚本实例** | 脚本 + 参数 = 一个独立的 RSS 订阅源 |
| **RSS Token** | 每个实例唯一的订阅标识 |

### 编写你的第一个脚本

创建一个 `.py` 文件：

```python
NAME = "My Feed"
DESCRIPTION = "我的第一个 RSS 源"
PARAMS = [
    {"name": "keyword", "label": "关键词", "type": "string", "required": True},
]

async def run(params, context):
    # params = {"keyword": "..."}
    # 在这里获取数据并返回 RSS 条目
    return [
        {
            "title": "示例条目",
            "description": "这是描述",
            "link": "https://example.com",
        }
    ]
```

在前端上传此文件，创建实例，即可获取 RSS 订阅地址。

## 🏗 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python / FastAPI |
| 数据库 | SQLite (via aiosqlite) |
| 任务调度 | APScheduler |
| 前端 | Vue 3 + TypeScript |
| UI | Naive UI |
| 部署 | Docker + Docker Compose |

## 📄 文档

详细文档请见 `docs/` 目录：

- [部署指南](docs/deployment.md)
- [脚本开发指南](docs/script-development.md)
- [API 参考](docs/api-reference.md)

## 📝 License

MIT
