# 用户脚本开发指南

## 脚本规范 v1.0

每个用户脚本是一个标准的 Python 文件，遵循以下规范。

### 必需导出

```python
NAME = "脚本名称"          # str - 脚本名称
DESCRIPTION = "脚本描述"    # str - 脚本描述

async def run(params: dict, context: dict) -> list[dict]:
    """主函数，返回 RSS 条目列表。"""
    ...
```

### 可选导出

```python
VERSION = "1.0.0"          # str - 版本号
AUTHOR = "作者名"           # str - 作者

PARAMS = [...]             # list[dict] - 参数定义
SCHEDULE = {...}           # dict - 默认调度配置
```

### 参数定义 (PARAMS)

```python
PARAMS = [
    {
        "name": "username",           # 参数名 (必填)
        "label": "用户名",            # 显示标签 (必填)
        "type": "string",             # 类型: string, number, boolean, select, multiline, password
        "required": True,             # 是否必填
        "default": "",                # 默认值
        "description": "请输入用户名", # 说明
        "options": [                  # select 类型的选项
            {"label": "选项1", "value": "opt1"},
        ],
    },
]
```

### 调度配置 (SCHEDULE)

```python
# 间隔触发
SCHEDULE = {
    "type": "interval",
    "interval_minutes": 60,
}

# 定时触发 (支持多时间点)
SCHEDULE = {
    "type": "cron",
    "cron_expressions": ["0 8 * * *", "0 18 * * *"],
}

# 刷新触发 (访问 RSS 时按需更新)
SCHEDULE = {
    "type": "on_refresh",
    "refresh_interval_minutes": 30,
}

# 手动触发
SCHEDULE = {
    "type": "manual",
}
```

### RSS 条目格式

`run()` 函数必须返回一个字典列表，每个字典格式如下:

```python
{
    "title": "条目标题",          # 必需 - 标题
    "description": "条目描述",     # 必需 - 描述/摘要
    "link": "https://...",        # 必需 - 原文链接
    "guid": "unique-id",          # 可选 - 唯一标识 (默认使用 link)
    "pub_date": "2024-01-01T00:00:00Z",  # 可选 - ISO 8601 日期
    "author": "作者名",            # 可选 - 作者
    "categories": ["标签1"],       # 可选 - 分类标签
    "content": "完整内容",          # 可选 - 完整文章内容
    "image": "https://...",       # 可选 - 图片 URL
}
```

### 脚本上下文

`run()` 的第二个参数 `context` 包含:

```python
context = {
    "logger": {
        "info": lambda msg: ...,   # 日志记录
        "error": lambda msg: ...,
    },
    "data_dir": ".",               # 数据目录 (可用于缓存)
}
```

## 完整示例

### GitHub Releases 获取

```python
NAME = "GitHub Releases"
DESCRIPTION = "获取指定仓库的最新 Releases"
VERSION = "1.0.0"

PARAMS = [
    {"name": "owner", "label": "仓库所有者", "type": "string", "required": True},
    {"name": "repo", "label": "仓库名", "type": "string", "required": True},
]

SCHEDULE = {"type": "interval", "interval_minutes": 60}

async def run(params, context):
    import httpx
    url = f"https://api.github.com/repos/{params['owner']}/{params['repo']}/releases"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        releases = resp.json()

    items = []
    for rel in releases:
        items.append({
            "title": f"{params['repo']} {rel['tag_name']}",
            "description": (rel.get("body") or "")[:300],
            "link": rel["html_url"],
            "pub_date": rel["published_at"],
            "author": rel["author"]["login"],
            "categories": ["release"],
        })
    return items
```

## 开发调试技巧

1. **本地测试**: 先单独在本地运行脚本，确认逻辑正确
2. **使用 `context["logger"]`**: 记录日志帮助调试
3. **异常处理**: 做好 try/except，避免整个任务失败
4. **超时控制**: 使用 `httpx` 的 `timeout` 参数，避免长时间挂起
5. **返回数据量**: 控制返回条目数 (建议不超过 50)，`max_items` 可在实例配置中调整
