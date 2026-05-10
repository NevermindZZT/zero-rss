# 部署指南

## Docker Compose 部署

zero-rss 支持两种 Docker Compose 部署方式：

- 源码构建版：使用本地 `backend/` 和 `frontend/` 目录构建镜像，适合开发或验证
- 镜像部署版：直接拉取 Docker Hub 已构建镜像，适合生产或快速部署

### A. 源码构建版 (推荐用于本地开发)

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，修改以下关键配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AUTH_TOKEN` | 访问令牌 (必须修改!) | `your-secret-token-here` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `SCRIPT_TIMEOUT` | 脚本超时秒数 | `60` |

### 2. 启动

```bash
docker compose up -d
```

### 3. 访问

- **前端管理界面**: http://localhost:11081
- **API 文档**: http://localhost:11080/docs
- **健康检查**: http://localhost:11080/api/system/health

### 4. 停止

```bash
docker compose down
```

如果要同时删除数据:

```bash
docker compose down -v
```

### B. 镜像部署版 (使用 Docker Hub 镜像)

如果你已经通过 GitHub Actions 发布了镜像，可以直接拉取并部署。

本项目的示例 Docker Hub 仓库用户名是 `nevermindzzt`：

- `nevermindzzt/zero-rss-backend`
- `nevermindzzt/zero-rss-frontend`

#### 1. 配置环境变量

```bash
cp .env.example .env
```

建议至少确认以下变量：

```bash
AUTH_TOKEN=your-secret-token-here
DOCKERHUB_USERNAME=nevermindzzt
APP_VERSION=1.1.0
EXTERNAL_URL=
```

#### 2. 启动镜像版 Compose

```bash
docker compose -f docker-compose.image.yml up -d
```

如果想先拉取最新镜像：

```bash
docker compose -f docker-compose.image.yml pull
docker compose -f docker-compose.image.yml up -d
```

#### 3. 升级版本

当发布新版本 tag 后，只需更新 `.env` 里的版本号，然后重新拉取镜像：

```bash
APP_VERSION=1.1.1
docker compose -f docker-compose.image.yml pull
docker compose -f docker-compose.image.yml up -d
```

## 数据持久化

数据存储在 Docker 卷 `rss-data` 中:
- SQLite 数据库文件: `/app/data/rss.db`
- 脚本目录: `/app/scripts` (映射自 `./examples/scripts/`)

镜像部署版与源码构建版共用同一个数据卷和脚本挂载方式。

## 反向代理配置

### Nginx (HTTPS)

```nginx
server {
    listen 443 ssl;
    server_name rss.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:11081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:11080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    location /rss/ {
        proxy_pass http://127.0.0.1:11080;
        proxy_set_header Host $host;
        proxy_read_timeout 120s;
    }
}
```

## 环境变量参考

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AUTH_TOKEN` | API 访问令牌 | `your-secret-token-here` |
| `DATABASE_URL` | 数据库连接 URL | `sqlite+aiosqlite:///data/rss.db` |
| `SCRIPTS_DIR` | 用户脚本目录 | `/app/scripts` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `HOST` | 监听地址 | `0.0.0.0` |
| `PORT` | 监听端口 | `11080` |
| `EXTERNAL_URL` | 外部访问地址 (用于 RSS 链接) | `""` |
| `SCRIPT_TIMEOUT` | 脚本执行超时(秒) | `60` |
