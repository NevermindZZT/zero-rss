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

### RSS 属性说明 (推荐作为开发时速查表)

| 属性 | 是否必填 | 类型 | 含义 | 当前 XML 输出情况 |
|---|---|---|---|---|
| `title` | 必填 | `str` | 条目标题，读者第一眼看到的文本 | 输出为 `<title>` |
| `description` | 必填 | `str` | 条目摘要/主体内容（建议放主要可读内容） | 输出为 `<description>` |
| `link` | 必填 | `str(URL)` | 原文链接/详情页链接 | 输出为 `<link>` |
| `guid` | 可选 | `str` | 条目唯一标识，建议全局稳定不变 | 输出为 `<guid>`；为空时回退 `link` |
| `pub_date` | 可选 | `str(ISO 8601)` | 发布时间，例如 `2026-05-10T08:00:00Z` | 输出为 `<pubDate>`（解析失败会忽略） |
| `author` | 可选 | `str` | 作者/发布者 | 输出为 `<author>` |
| `categories` | 可选 | `list[str]` | 分类标签 | 每项输出为 `<category>` |
| `content` | 可选 | `str` | 完整正文（扩展字段） | 当前实现仅入库，默认不写入 XML |
| `image` | 可选 | `str(URL)` | 封面图地址（扩展字段） | 当前实现仅入库，默认不写入 XML |

> 兼容性建议: 若你希望读者在 RSS 阅读器里直接看到主体内容，请把主体内容放在 `description`。`content`/`image` 可作为未来扩展字段保留。

### 内容主体应该如何处理 (美观易读)

`description` 必须使用富文本（HTML）输出，采用"标题 + 摘要 + 关键点 + 结尾链接"结构，避免一整段长文本。

推荐原则：

1. **先摘要再细节**: 第一段给 1~2 句核心信息。
2. **分段清晰**: 使用空行分段，单段控制在 2~4 行。
3. **信息可扫描**: 关键点用短列表（每行一个要点）。
4. **长度可控**: 建议 150~600 字；超长正文截断并加"查看全文"提示。
5. **容错优先**: 远程数据为空时填充占位文本，避免空 `description`。

### 富文本格式规范 (HTML)

`description` 字段统一使用轻量 HTML 片段，推荐并要求如下：

1. **段落**: 使用 `<p>` 做分段，不用纯 `\n` 作为主要排版手段。
2. **重点**: 使用 `<strong>` 标注关键词或核心结论。
3. **列表**: 使用 `<ul><li>...</li></ul>` 表达要点。
4. **链接**: 使用 `<a href="https://..." target="_blank" rel="noopener noreferrer">...</a>`。
5. **换行**: 仅在段内短换行时使用 `<br>`，不要连续堆叠 `<br><br><br>`。

允许标签（白名单建议）：

- `<p>` `<strong>` `<em>` `<ul>` `<ol>` `<li>` `<a>` `<br>` `<code>`

禁止内容：

- `<script>`、内联事件（如 `onclick`）、`javascript:` 协议链接
- 大段未转义原始 HTML 片段拼接

### 主体排版硬性约束 (必须遵守)

1. **必须使用富文本 HTML**: 不允许仅输出纯文本长串。
2. **禁止单行直出全文**: `description` 不能把所有内容拼成一行。
3. **必须有结构化换行**: 至少拆成 2 段（摘要段 + 详情段/要点段）。
4. **必须体现重点**: 至少 1 处重点文本，使用 `<strong>重点</strong>`。
5. **链接必须是超链接形式**: 使用 `<a href="https://...">查看全文</a>`，不能只放裸 URL。
6. **链接必须可跳转**: `href` 必须是完整绝对地址（`http://` 或 `https://`）。
7. **列表信息必须可读**: 多要点内容使用 `<ul><li>...</li></ul>`，不要逗号长串。
8. **链接安全属性**: 外链建议带 `target="_blank" rel="noopener noreferrer"`。

不合格示例（禁止）：

```python
description = f"{summary} {detail} {url}"
```

合格示例（推荐 HTML 结构）：

```python
description = (
    f"<p><strong>摘要</strong>: {summary}</p>"
    f"<p><strong>关键要点</strong>:</p>"
    f"<ul>{''.join(f'<li>{x}</li>' for x in highlights[:5])}</ul>"
    f"<p><a href='{link}' target='_blank' rel='noopener noreferrer'>查看全文</a></p>"
)
```

可直接复用的主体模板（富文本，推荐）：

```python
summary = (item.get("summary") or "").strip()
highlights = item.get("highlights") or []
link = item.get("url") or ""

def esc(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

summary_html = esc(summary) or "暂无摘要"
list_html = "".join(f"<li>{esc(x)}</li>" for x in highlights[:5])

description = (
    f"<p><strong>摘要</strong>: {summary_html}</p>"
    f"<p><strong>关键要点</strong>:</p>"
    f"<ul>{list_html}</ul>"
    f"<p><a href='{link}' target='_blank' rel='noopener noreferrer'>查看全文</a></p>"
)
```

### 生成质量检查清单

- `title/description/link` 均非空
- `guid` 稳定（同一条内容多次抓取不变化）
- `pub_date` 为标准 ISO 8601 或留空
- `description` 无大段乱码/无意义重复
- `description` 使用富文本 HTML（而非纯文本长串）
- `description` 至少 2 段，且不是单行大串
- 至少 1 处重点标注（`<strong>...</strong>`）
- 包含可点击超链接（`<a href="https://...">...</a>`）
- 外链包含 `target` 和 `rel` 安全属性
- 列表数量适中（建议单次返回不超过 50 条）

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

## 本地测试方法 (可复用到其他项目)

为了让这个脚本规范可以在其他项目复用，建议把"脚本本地测试"分成两层：

1. 快速冒烟：直接执行单个脚本，看是否能返回合法 RSS 条目列表。
2. 自动化回归：用 pytest 固化参数和期望，避免后续改动破坏行为。

### 1) 最小本地测试器 (smoke test)

在任意项目新建一个测试器文件，例如 `tools/test_user_script.py`：

```python
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path


def load_module(script_path: str):
    path = Path(script_path).resolve()
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def validate_items(items):
    if not isinstance(items, list):
        raise AssertionError("run() must return list[dict]")
    required = {"title", "description", "link"}
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise AssertionError(f"item[{i}] must be dict")
        missing = required - set(item.keys())
        if missing:
            raise AssertionError(f"item[{i}] missing fields: {sorted(missing)}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("script", help="Path to user script .py")
    parser.add_argument("--params", default="{}", help="JSON params")
    args = parser.parse_args()

    params = json.loads(args.params)
    module = load_module(args.script)

    # 协议检查
    assert hasattr(module, "NAME"), "Missing NAME"
    assert hasattr(module, "DESCRIPTION"), "Missing DESCRIPTION"
    assert hasattr(module, "run"), "Missing run(params, context)"

    logs = []
    context = {
        "logger": {
            "info": lambda m: logs.append(("info", str(m))),
            "error": lambda m: logs.append(("error", str(m))),
        },
        "data_dir": ".tmp-script-data",
    }

    result = module.run(params, context)
    if asyncio.iscoroutine(result):
        result = await result

    validate_items(result)

    print(json.dumps({"ok": True, "count": len(result), "logs": logs[:10]}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
```

### Skill 内置工具脚本 (推荐直接调用)

本 skill 已内置可复用测试器：

- `.github/skills/zero-rss-script-dev/tools/test_user_script.py`

直接调用示例：

```bash
python .github/skills/zero-rss-script-dev/tools/test_user_script.py examples/scripts/github_releases.py --params '{"owner":"microsoft","repo":"vscode","max_releases":3}' --min-items 1
```

使用参数文件示例：

```bash
python .github/skills/zero-rss-script-dev/tools/test_user_script.py examples/scripts/github_releases.py --params-file .github/skills/zero-rss-script-dev/examples/github_releases.params.json --timeout 20
```

运行示例：

```bash
python tools/test_user_script.py examples/scripts/github_releases.py --params '{"owner":"microsoft","repo":"vscode","max_releases":3}'
```

通过标准：

- 脚本可加载
- `NAME` / `DESCRIPTION` / `run` 存在
- `run()` 返回 `list[dict]`
- 每个条目至少包含 `title`、`description`、`link`

### 2) pytest 回归测试模板

如果项目已使用 pytest，建议补一个最小回归用例：

```python
import asyncio
import importlib.util
from pathlib import Path


def _load(path: str):
    p = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(p.stem, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_user_script_contract():
    mod = _load("examples/scripts/github_releases.py")
    assert hasattr(mod, "NAME")
    assert hasattr(mod, "DESCRIPTION")
    assert hasattr(mod, "run")

    ctx = {"logger": {"info": lambda _: None, "error": lambda _: None}, "data_dir": ".tmp-script-data"}
    params = {"owner": "microsoft", "repo": "vscode", "max_releases": 2}

    result = mod.run(params, ctx)
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)

    assert isinstance(result, list)
    for item in result:
        assert "title" in item
        assert "description" in item
        assert "link" in item
```

## 跨项目复用建议

- 保持脚本协议稳定：`NAME`、`DESCRIPTION`、`run(params, context)` 不变。
- 将 `tools/test_user_script.py` 作为模板复制到新项目，保证最小可用测试能力。
- CI 中至少运行一次脚本契约测试，避免脚本上传后才暴露错误。

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
