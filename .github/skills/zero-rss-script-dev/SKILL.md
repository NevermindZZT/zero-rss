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
    "description": "条目描述",      # 必需 - 摘要/预览（HTML 实体编码，见下方说明）
    "link": "https://...",         # 必需 - 原文链接
    "guid": "unique-id",           # 可选 - 唯一标识, 默认按内容自动生成
    "pub_date": "2024-01-01T00:00:00Z",  # 可选 - ISO 8601 日期
    "author": "作者名",             # 可选 - 作者
    "categories": ["标签1"],        # 可选 - 分类标签
    "content": "完整内容",           # 可选 - 完整正文（CDATA 包裹输出为 <content:encoded>）
    "image": "https://...",        # 可选 - 图片 URL
}
```

### RSS 属性说明 (推荐作为开发时速查表)

| 属性 | 是否必填 | 类型 | 含义 | XML 输出方式 |
|---|---|---|---|---|
| `title` | 必填 | `str` | 条目标题，读者第一眼看到的文本 | `<title>`（原样输出） |
| `description` | 必填 | `str` | 条目摘要/简短预览（HTML 实体编码） | `<description>`（HTML 实体编码） |
| `link` | 必填 | `str(URL)` | 原文链接/详情页链接 | `<link>` |
| `guid` | 可选 | `str` | 条目唯一标识，建议全局稳定不变 | `<guid>`；为空时按内容自动生成 |
| `pub_date` | 可选 | `str(ISO 8601)` | 发布时间，例如 `2026-05-10T08:00:00Z` | `<pubDate>`（缺失/无效则回退为抓取时间） |
| `author` | 可选 | `str` | 作者/发布者 | `<author>` |
| `categories` | 可选 | `list[str]` | 分类标签 | 每项输出为 `<category>` |
| `content` | 可选 | `str` | **完整正文（富文本 HTML）** | **`<content:encoded>`**（CDATA 包裹，与 `<description>` 并存） |
| `image` | 可选 | `str(URL)` | 封面图地址（扩展字段） | 当前仅入库，预留 |

> **核心原则**: `description` = 摘要/预览（HTML 实体编码），`content` = 完整正文（CDATA 包裹在 `<content:encoded>` 中）。详见下方说明。

### 内容输出规范

RSS 2.0 本质是 XML，直接嵌入 HTML 标签会破坏文档结构。系统使用两种互补的技术安全传递富文本：

| 技术 | 输出位置 | 适用场景 | 编码方式 |
|---|---|---|---|
| **HTML 实体编码** | `<description>` | 简短摘要/预览 | 将 `<` `>` `&` 替换为 `&lt;` `&gt;` `&amp;`，最安全、广泛兼容 |
| **CDATA 区块** | `<content:encoded>` | 完整正文/富文本全文 | `<![CDATA[ ... ]]>` 包裹，XML 解析器原样读取 |

当脚本同时提供 `description` 和 `content` 时，系统会输出**两条并存的字段**：

```xml
<item>
  <title>示例标题</title>
  <description>这是摘要：欢迎来到&lt;strong&gt;示例&lt;/strong&gt;博客</description>
  <content:encoded><![CDATA[<p>这是完整正文，包含<strong>加粗</strong>和<em>斜体</em>。</p>]]></content:encoded>
  <link>https://example.com/article</link>
  <pubDate>Sun, 10 May 2026 08:00:00 +0000</pubDate>
</item>
```

#### description — 摘要（HTML 实体编码）

- 用途：**简短预览**，RSS 阅读器列表页直接展示
- 编码：HTML 实体编码（`<` → `&lt;`），确保 XML 结构安全
- 长度建议：150~300 字，关键信息前置
- 无 `content` 时：`description` 也可以承载完整主体（推荐仍用富文本 HTML 实体编码）

#### content — 完整正文（CDATA + content:encoded）

- 用途：**完整文章正文**，RSS 阅读器详情页展示
- 编码：`<![CDATA[ ... ]]>` 包裹，XML 解析器原样读取，无需转义 HTML 标签
- 适合内容：带大量 HTML 标签的全正文、含代码块的长文、图文混排
- 阅读器表现：成熟 RSS 客户端（如 Feedly、NetNewsWire）优先展示 `<content:encoded>`

> 如果只填写 `description`，系统会将其作为唯一输出字段。  
> 如果只填写 `content`，系统会将其同时放入 `<description>`（CDATA 包裹）和 `<content:encoded>`。  
> **推荐同时填写二者**：`description` 放摘要，`content` 放全文。

### Markdown 模板处理能力（新增）

如果你以 Markdown 写作，建议统一采用以下流水线：

1. Markdown 模板 + 变量渲染（如 `{{title}}`、`{{summary}}`）
2. Markdown 转 HTML（正文）
3. 生成摘要（优先首段）
4. `description` 放摘要 HTML（会实体编码）
5. `content` 放完整 HTML（会进入 `<content:encoded><![CDATA[...]]></content:encoded>`）

推荐依赖（可选）：

```bash
pip install markdown-it-py mdit-py-plugins bleach
```

可直接复用的最小实现：

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

try:
    import bleach
except ImportError:
    bleach = None


_md = (
    MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})
    .use(footnote_plugin)
    .use(tasklists_plugin)
)


ALLOWED_TAGS = [
    "p", "strong", "em", "ul", "ol", "li", "a", "code", "pre", "blockquote",
    "img", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "table", "thead", "tbody",
    "tr", "th", "td", "span", "div"
]

ALLOWED_ATTRS = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "span": ["style"],
    "div": ["style"],
    "p": ["style"],
    "td": ["style"],
    "th": ["style"],
}


def _sanitize_html(html: str) -> str:
    """对 Markdown 转换后的 HTML 做安全过滤。"""
    if bleach is None:
        return html
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=["http", "https", "mailto"],
        strip=True,
    )


def render_markdown(markdown_text: str) -> str:
    html = _md.render(markdown_text or "")
    return _sanitize_html(html)


def first_paragraph_as_summary(html: str, fallback: str = "暂无摘要") -> str:
    """提取首段作为 description，避免直接塞整篇全文。"""
    marker_start = html.find("<p")
    if marker_start == -1:
        return f"<p>{fallback}</p>"
    marker_end = html.find("</p>", marker_start)
    if marker_end == -1:
        return f"<p>{fallback}</p>"
    return html[marker_start: marker_end + 4]


def build_rss_fields_from_markdown(md_template: str, variables: dict[str, Any]) -> tuple[str, str]:
    """
    返回 (description_html, content_html)
    - description_html: 摘要（短）
    - content_html: 正文（完整）
    """
    # 简单模板替换，可替换为 jinja2
    md = md_template
    for k, v in variables.items():
        md = md.replace("{{" + k + "}}", str(v))

    content_html = render_markdown(md)
    description_html = first_paragraph_as_summary(content_html)
    return description_html, content_html
```

在 `run()` 中使用：

```python
description_html, content_html = build_rss_fields_from_markdown(md_template, data)

return [{
    "title": data["title"],
    "description": description_html,
    "content": content_html,
    "link": data["url"],
    "pub_date": data.get("pub_date"),
}]
```

### CSS 样式策略（新增）

RSS 客户端对 CSS 的支持差异极大，建议采用“兼容分级”策略：

1. 第一优先：语义标签（`p/ul/li/blockquote/code/table`）
2. 第二优先：关键样式用内联 `style="..."`
3. 谨慎使用：`<style>` 内嵌样式（不少客户端会过滤）
4. 不建议：外链 CSS、复杂布局（grid/flex 在部分客户端失效）

推荐做法：给 `content` 包一层轻量样式容器，所有关键视觉都写内联。

```python
def wrap_with_rss_style(content_html: str) -> str:
    return (
        '<div style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif;'
        ' line-height: 1.7; color: #1f2937; font-size: 15px;">'
        + content_html +
        '</div>'
    )
```

可选主题片段（建议只用于 `content`，不要塞进 `description`）：

```python
CARD_NOTE = (
    '<div style="padding:12px 14px;border:1px solid #e5e7eb;border-radius:10px;'
    'background:#f8fafc;margin:12px 0;">'
    '<strong style="color:#0f172a;">提示：</strong>'
    '<span style="color:#334155;">这里是重点说明。</span>'
    '</div>'
)
```

样式兼容建议：

- `description` 保持“轻样式+短文本”，避免过多内联样式。
- `content` 可使用适量内联样式增强观感。
- 图片务必带 `width/height/alt`，避免客户端布局跳动。
- 避免依赖暗色模式媒体查询，很多客户端不支持。
- 避免依赖 `<style>` 和 class 选择器，优先内联 style。

### 关于 XSLT 的建议

`<?xml-stylesheet ...?>` 主要对浏览器直接打开 XML 时有效，对多数 RSS 客户端无效或被忽略。  
它可以作为“调试/展示层”补充，但不应作为阅读器排版的主路径。

### 内容主体排版建议 (美观易读)

`description` 和 `content` 都应使用富文本（HTML）输出，但二者职责不同：

| 维度 | `description`（摘要） | `content`（全文） |
|---|---|---|
| 定位 | RSS 阅读器列表页的预览 | RSS 阅读器详情页的完整阅读体验 |
| 长度 | 150~300 字 | 不限，可包含完整正文 |
| 结构 | "摘要段 + 要点 + 查看全文链接" | 完整文章结构 |
| 编码 | HTML 实体编码 | CDATA 包裹 |

#### description 排版原则

1. **先摘要再细节**: 第一段给 1~2 句核心信息。
2. **分段清晰**: 使用空行分段，单段控制在 2~4 行。
3. **信息可扫描**: 关键点用短列表（每行一个要点）。
4. **长度可控**: 建议 150~300 字；超长内容用 `content` 放全文。
5. **容错优先**: 远程数据为空时填充占位文本，避免空 `description`。
6. **链接引导**: 结尾必须有"查看全文"链接。

> `content` 的排版无需特别约束，它使用 `<![CDATA[ ... ]]>` 包裹完整的 HTML 正文即可，可以包含任意复杂度的 HTML 标签。

### 富文本格式规范 (HTML)

所有 HTML 内容遵循以下规则：

1. **段落**: 使用 `<p>` 做分段，不用纯 `\n` 作为主要排版手段。
2. **重点**: 使用 `<strong>` 标注关键词或核心结论。
3. **列表**: 使用 `<ul><li>...</li></ul>` 表达要点（**不要使用 `<ol>` 自动编号，见下方说明**）。
4. **链接**: 使用 `<a href="https://..." target="_blank" rel="noopener noreferrer">...</a>`。
5. **换行**: **禁止使用 `<br>` 进行多行换行**（见下方说明），改用 `<p>` 标签分段。
6. **图片**: `<img src="https://..." alt="描述">`（推荐在 `content` 中使用）。

#### 换行问题：禁止使用 `<br>` 做主要分段

**问题背景**: 某些 RSS 客户端对 `<br>` 的渲染支持不完整，导致内容不换行甚至显示错乱。

**禁止写法**：
```html
<li>项目 1<br>详情信息<br>更多内容</li>
```

**推荐写法**：改用 `<p>` 或 `<div>` 分段：
```html
<p>项目 1</p>
<p>详情信息</p>
<p>更多内容</p>
```

**例外**：仅在段内单行短连接时可使用 `<br>`（如地址的"市/街道/号"），避免连续多个 `<br>`。

#### 列表编号问题：禁止使用 `<ol>` 自动编号

**问题背景**: 当文本内容中已包含序号（如"1. 项目1"、"2. 项目2"），RSS 客户端的 `<ol>` 标签会自动添加序号，导致显示为"1.1. 项目1"等重复编号。

**禁止写法**：
```html
<ol>
  <li>1. 项目名称<br>细节信息</li>
  <li>2. 项目名称<br>细节信息</li>
</ol>
```

**推荐写法 1**：改用无序列表 `<ul>`：
```html
<ul>
  <li>1. 项目名称</li>
  <li>2. 项目名称</li>
</ul>
```

**推荐写法 2**：改用 `<div>` 或 `<p>` 分段，纯文本序号：
```html
<p><strong>1. 项目名称</strong></p>
<p>细节信息</p>
<p><strong>2. 项目名称</strong></p>
<p>细节信息</p>
```

**原则**: 如果内容本身已经有"1. 2. 3."文本序号，就用 `<ul>` 或 `<div>`，不要让 HTML 标签再加一层自动序号。

允许标签（白名单建议）：

- `<p>` `<strong>` `<em>` `<ul>` `<li>` `<a>` `<code>` `<pre>` `<img>` `<blockquote>` `<div>`
- **不建议**: `<ol>`（除非确信内容中无文本序号）、`<br>`（改用 `<p>` 分段）

禁止内容：

- `<script>`、内联事件（如 `onclick`）、`javascript:` 协议链接
- 大段未转义原始 HTML 片段拼接（会破坏 XML 结构）
- `description` 中不要放超大 HTML（会降低列表页性能）

### 主体排版硬性约束 (必须遵守)

1. **必须使用富文本 HTML**: 不允许仅输出纯文本长串。
2. **禁止单行直出全文**: `description` 不能把所有内容拼成一行。
3. **必须有结构化换行**: 至少拆成 2 段（摘要段 + 详情段/要点段）。
4. **必须体现重点**: 至少 1 处重点文本，使用 `<strong>重点</strong>`。
5. **链接必须是超链接形式**: 使用 `<a href="https://...">查看全文</a>`，不能只放裸 URL。
6. **链接必须可跳转**: `href` 必须是完整绝对地址（`http://` 或 `https://`）。
7. **列表信息必须可读**: 多要点内容使用 `<ul><li>...</li></ul>`，不要逗号长串。
8. **链接安全属性**: 外链建议带 `target="_blank" rel="noopener noreferrer"`。
9. **禁止用 `<br>` 进行多行换行**: 改用 `<p>` 分段以保证在所有 RSS 客户端上正确显示。
10. **禁止用 `<ol>` 当文本含序号**: 如果内容文本本身已有"1. 2. 3."格式，改用 `<ul>` 或 `<p>` 分段避免序号重复。
11. **`description` 使用 HTML 实体编码**: 脚本只需输出合法 HTML 文本，实体编码由系统处理。
12. **`content` 使用 CDATA 包裹**: 脚本输出原始 HTML 即可，无需额外转义。

不合格示例（禁止）：


```python
description = f"{summary} {detail} {url}"
```

合格示例（推荐 HTML 结构）：

```python
# description：使用 HTML 实体编码（esc 函数见下方）
description = (
    f"<p><strong>摘要</strong>: {summary}</p>"
    f"<p><strong>关键要点</strong>:</p>"
    f"<ul>{''.join(f'<li>{x}</li>' for x in highlights[:5])}</ul>"
    f"<p><a href='{link}' target='_blank' rel='noopener noreferrer'>查看更多</a></p>"
)

# content：完整正文，系统会自动用 CDATA 包裹放入 <content:encoded>
content = (
    f"<h2>详细内容</h2>"
    f"{full_body_html}"
)

# 返回时同时包含两个字段
return [
    {
        "title": title,
        "description": description,  # → <description>（HTML 实体编码）
        "content": content,          # → <content:encoded>（CDATA 包裹）
        "link": link,
    }
]
```

可直接复用的主体模板（富文本，推荐）：

```python
# --- HTML 实体编码工具函数（用于 description） ---
def esc(text: str) -> str:
    """将 HTML 特殊字符转为 XML 实体编码，确保 description 中 XML 结构安全。"""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

# --- description 模板（HTML 实体编码，用于摘要/预览） ---
summary = (item.get("summary") or "").strip()
highlights = item.get("highlights") or []
link = item.get("url") or ""

summary_html = esc(summary) or "暂无摘要"
list_html = "".join(f"<li>{esc(x)}</li>" for x in highlights[:5])

description = (
    f"<p><strong>摘要</strong>: {summary_html}</p>"
    f"<p><strong>关键要点</strong>:</p>"
    f"<ul>{list_html}</ul>"
    f"<p><a href='{link}' target='_blank' rel='noopener noreferrer'>查看全文</a></p>"
)

# --- content 模板（原始 HTML，放入 CDATA 区块，可包含完整正文） ---
body_html = item.get("body") or item.get("content_html") or ""
content = (
    f"<h2>{esc(summary)}</h2>"
    f"{body_html}"
    f"<p><a href='{link}'>原文链接</a></p>"
)

# 最后返回：
return [
    {
        "title": item.get("title") or "无标题",
        "description": description,      # 摘要（HTML 实体编码）
        "content": content,              # 完整正文（放入 <content:encoded> CDATA）
        "link": link,
        "pub_date": item.get("pub_date"),
        "author": item.get("author"),
        "categories": item.get("categories", []),
    }
]
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
- **`description` 和 `content` 分工合理**：前者是摘要+HTML实体编码，后者是全文+CDATA
- **`content` 不为空时，其中 HTML 应是完整可读的文章正文**
- **`content` 中不要包含 `<script>` 或内联事件**

---

> **最后提醒**: 你不需要在脚本里自己包裹 `CDATA` 或做实体编码的二次转义。系统后端会自动处理：
> - `description` → HTML 实体编码后放入 `<description>`
> - `content` → CDATA 包裹后放入 `<content:encoded>`
>
> 你只需输出合法的 HTML 字符串即可。

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

导出独立 HTML 报告（用于本地直接验证 RSS 内容渲染）：

```bash
python .github/skills/zero-rss-script-dev/tools/test_user_script.py examples/scripts/github_releases.py --params '{"owner":"microsoft","repo":"vscode","max_releases":3}' --html-output .tmp/rss-test-report.html
```

生成后可直接用浏览器打开 `.tmp/rss-test-report.html`，查看每条 item 的：

- `description` 渲染预览与原始文本
- `content` 渲染预览与原始文本
- 测试日志与参数快照

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
