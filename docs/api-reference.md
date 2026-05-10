# API 参考

## 基础信息

- **Base URL**: `http://localhost:11080`
- **认证**: `Authorization: Bearer <token>`
- **RSS 订阅端点**: 无需认证
- **交互式文档**: `http://localhost:11080/docs`

## 认证

### 验证 Token

```
POST /api/system/auth
Content-Type: application/json

{"token": "your-token"}
```

**响应:**
```json
{"success": true, "message": "Authentication successful"}
```

## 系统

### 健康检查 (公开)

```
GET /api/system/health
```

**响应:**
```json
{"status": "ok", "version": "1.0.0"}
```

### 系统统计

```
GET /api/system/stats
Authorization: Bearer <token>
```

**响应:**
```json
{
    "total_scripts": 5,
    "total_instances": 12,
    "total_items": 350,
    "enabled_instances": 10,
    "recent_errors": 2
}
```

## 脚本模板管理

### 获取脚本列表

```
GET /api/scripts?search=github
Authorization: Bearer <token>
```

### 上传脚本

```
POST /api/scripts
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <script.py>
```

### 获取脚本详情

```
GET /api/scripts/:id
Authorization: Bearer <token>
```

### 更新脚本

```
PUT /api/scripts/:id
Authorization: Bearer <token>
Content-Type: application/json

{"code": "..."}
```

### 删除脚本

```
DELETE /api/scripts/:id
Authorization: Bearer <token>
```

## 实例管理

### 获取实例列表

```
GET /api/instances?script_id=xxx
Authorization: Bearer <token>
```

### 创建实例

```
POST /api/instances
Authorization: Bearer <token>
Content-Type: application/json

{
    "script_id": "uuid",
    "name": "My Instance",
    "description": "...",
    "params": {"key": "value"},
    "schedule_type": "interval",
    "schedule_config": {"interval_minutes": 60},
    "max_items": 100
}
```

### 获取实例详情

```
GET /api/instances/:id
Authorization: Bearer <token>
```

### 更新实例

```
PUT /api/instances/:id
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "New Name",
    "params": {"key": "new_value"},
    "enabled": true
}
```

### 删除实例

```
DELETE /api/instances/:id
Authorization: Bearer <token>
```

### 手动运行

```
POST /api/instances/:id/run
Authorization: Bearer <token>
```

### 测试运行 (不保存)

```
POST /api/instances/:id/test
Authorization: Bearer <token>
```

### 运行历史

```
GET /api/instances/:id/history?page=1&page_size=20
Authorization: Bearer <token>
```

### RSS 条目列表

```
GET /api/instances/:id/items?page=1&page_size=20
Authorization: Bearer <token>
```

## RSS 订阅 (公开)

### 获取 RSS XML

```
GET /rss/:token.xml
```

**响应:** `Content-Type: application/rss+xml`
标准的 RSS 2.0 XML。

如果实例配置了 `on_refresh` 调度且数据过期，会自动触发更新后再返回。
