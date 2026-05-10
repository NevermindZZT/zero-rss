# 快速开始

## 前置要求

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- 或 Python 3.11+ (开发模式)

## Docker 部署

### 1. 获取项目

```bash
git clone <your-repo-url>
cd zero-rss
```

### 2. 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，将 AUTH_TOKEN 改为你自己的安全令牌
# AUTH_TOKEN=your-secret-token-here
```

### 3. 上传你的脚本

将你的 Python 脚本放在 `examples/scripts/` 目录下:

```bash
# 示例: 上传一个脚本
cp my_script.py examples/scripts/
```

### 4. 启动

```bash
docker compose up -d
```

首次启动会自动:
- 构建后端 (FastAPI + SQLite)
- 构建前端 (Vue 3 + Naive UI)
- 初始化数据库
- 启动调度器

### 5. 访问

| 服务 | 地址 |
|------|------|
| 管理界面 | http://localhost:11081 |
| API 文档 | http://localhost:11080/docs |

### 6. 登录

1. 打开 http://localhost:11081
2. 输入你在 `.env` 中配置的 `AUTH_TOKEN`
3. 进入仪表盘

### 7. 添加你的第一个脚本

1. 点击「脚本管理」→「上传脚本」
2. 选择一个 `.py` 脚本文件
3. 上传后即可查看脚本详情和参数定义

### 8. 创建实例

1. 点击「实例管理」→「创建实例」
2. 选择脚本 → 配置参数 → 设置调度 → 创建
3. 获取 RSS 订阅地址，添加到你的 RSS 阅读器

## 开发模式

### 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器 (热重载)
uvicorn src.main:app --reload --host 0.0.0.0 --port 11080
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器默认代理 API 请求到 `http://localhost:11080`。

## 验证

- [ ] 前端页面正常加载 http://localhost:11081
- [ ] Token 登录成功
- [ ] 能上传 Python 脚本
- [ ] 能创建实例
- [ ] RSS 地址可用 (在阅读器中订阅)
- [ ] 手动运行正常
- [ ] 定时任务按计划执行
