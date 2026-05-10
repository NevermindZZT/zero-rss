# 部署指南

## Docker Compose 部署 (推荐)

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

## 数据持久化

数据存储在 Docker 卷 `rss-data` 中:
- SQLite 数据库文件: `/app/data/rss.db`
- 脚本目录: `/app/scripts` (映射自 `./examples/scripts/`)

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
