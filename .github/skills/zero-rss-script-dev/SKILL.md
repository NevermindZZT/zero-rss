---
name: zero-rss-script-dev
description: 'zero-rss 用户脚本开发指引。为用户编写 zero-rss Python 脚本提供完整规范、API 参考和最佳实践。当用户需要开发/修改/调试 zero-rss 用户脚本时使用，包含脚本协议定义、参数声明、调度配置、RSS 条目格式等。'
---

# zero-rss 用户脚本开发规范

zero-rss 用户脚本的核心概念：脚本模板 + 参数配置 = 一个独立 RSS 订阅源。

## 脚本规范 v1.0

每个用户脚本是一个标准的 Python 文件。

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

## 参数定义 (PARAMS)

系统会根据 PARAMS 自动在前端渲染动态表单。

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

支持的类型: `string`, `number`, `boolean`, `select`, `multiline`, `password`

## 调度配置 (SCHEDULE)

脚本可以声明默认调度计划，创建实例时用户可覆盖。

```python
# 间隔触发 - 每隔 N 分钟执行一次
SCHEDULE = {
    "type": "interval",
    "interval_minutes": 60,
}

# 定时触发 (支持多时间点)
SCHEDULE = {
    "type": "cron",
    "cron_expressions": ["0 8 * * *", "0 18 * * *"],
}

# 刷新触发 - 访问 RSS 时若数据过期则按需更新
SCHEDULE = {
    "type": "on_refresh",
    "refresh_interval_minutes": 30,
}

# 手动触发 - 仅在前端手动点击运行
SCHEDULE = {
    "type": "manual",
}
```

## RSS 条目格式

`run()` 必须返回字典列表, 每个字典:

```python
{
    "title": "条目标题",           # 必需 - 标题
    "description": "条目描述",      # 必需 - 描述/摘要
    "link": "https://...",         # 必需 - 原文链接
    "guid": "unique-id",           # 可选 - 唯一标识, 默认用 link
    "pub_date": "2024-01-01T00:00:00Z",  # 可选 - ISO 8601 日期
    "author": "作者名",             # 可选 - 作者
    "categories": ["标签1"],        # 可选 - 分类标签
    "content": "完整内容",           # 可选 - 完整文章内容
    "image": "https://...",        # 可选 - 图片 URL
}
```

## 脚本上下文

```python
context = {
    "logger": {
        "info": lambda msg: ...,   # 日志记录
        "error": lambda msg: ...,
    },
    "data_dir": ".",               # 数据目录 (可用于缓存)
}
```

## 开发调试技巧

1. **本地测试**: 先单独在本地运行脚本，确认逻辑正确
2. **使用 `context["logger"]`**: 记录日志帮助调试
3. **异常处理**: 做好 try/except，避免整个任务失败
4. **超时控制**: 使用 `httpx` 的 `timeout` 参数，避免长时间挂起
5. **返回数据量**: 控制返回条目数 (建议不超过 50)，可在实例配置中调整 `max_items`

## 完整示例

```python
"""
zero-rss 示例脚本: GitHub Releases

获取指定 GitHub 仓库的最新 Releases。
"""

NAME = "GitHub Releases"
DESCRIPTION = "获取指定 GitHub 仓库的最新 Releases 信息"
VERSION = "1.0.0"
AUTHOR = "zero-rss"

PARAMS = [
    {"name": "owner", "label": "仓库所有者", "type": "string", "required": True,
     "description": "GitHub 仓库所有者用户名"},
    {"name": "repo", "label": "仓库名", "type": "string", "required": True,
     "description": "GitHub 仓库名称"},
    {"name": "max_releases", "label": "最大数量", "type": "number", "required": False,
     "description": "获取的最大 Release 数量", "default": 10},
]

SCHEDULE = {"type": "interval", "interval_minutes": 60}

async def run(params, context):
    import httpx
    owner = params["owner"]
    repo = params["repo"]
    max_rel = int(params.get("max_releases", 10))
    url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page={max_rel}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"Accept": "application/vnd.github.v3+json"})
        resp.raise_for_status()
        releases = resp.json()

    items = []
    for rel in releases:
        items.append({
            "title": f"{repo} {rel['tag_name']}",
            "description": (rel.get("body") or "")[:300],
            "link": rel["html_url"],
            "guid": rel["html_url"],
            "pub_date": rel.get("published_at", ""),
            "author": rel.get("author", {}).get("login", ""),
            "categories": ["release", f"{owner}/{repo}"],
        })

    context["logger"]["info"](f"Got {len(items)} releases")
    return items
```

## 更多参考

- 项目示例脚本: `examples/scripts/github_releases.py`, `hacker_news.py`, `rss_proxy.py`
- 后端协议定义: `backend/src/core/protocol.py`
- 完整文档: `docs/script-development.md`
