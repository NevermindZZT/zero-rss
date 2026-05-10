"""
zero-rss 示例脚本: RSS 代理

将现有的 RSS/Atom 订阅源转换为 zero-rss 管理的格式。
可以添加过滤和内容处理逻辑。
"""

NAME = "RSS Proxy"
DESCRIPTION = "代理现有的 RSS/Atom 订阅源，支持内容过滤和转换"
VERSION = "1.0.0"
AUTHOR = "zero-rss"

PARAMS = [
    {
        "name": "source_url",
        "label": "源 RSS URL",
        "type": "string",
        "required": True,
        "description": "要代理的现有 RSS/Atom 订阅源地址",
        "default": "",
    },
    {
        "name": "max_items",
        "label": "最大条目数",
        "type": "number",
        "required": False,
        "description": "保留的最大条目数",
        "default": 50,
    },
    {
        "name": "filter_keyword",
        "label": "关键词过滤",
        "type": "string",
        "required": False,
        "description": "只包含标题或描述中包含此关键词的条目 (留空不过滤)",
        "default": "",
    },
]

SCHEDULE = {
    "type": "interval",
    "interval_minutes": 30,
}


async def run(params, context):
    """获取并解析源 RSS，返回 RSS 条目列表。"""
    import httpx
    from xml.etree import ElementTree

    source_url = params.get("source_url", "").strip()
    max_items = int(params.get("max_items", 50))
    filter_keyword = params.get("filter_keyword", "").strip().lower()

    if not source_url:
        raise ValueError("source_url 不能为空")

    context["logger"]["info"](f"Fetching RSS from {source_url}")

    async with httpx.AsyncClient() as client:
        resp = await client.get(source_url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        xml_content = resp.text

    # 解析 RSS/Atom
    root = ElementTree.fromstring(xml_content)
    items = []

    # 处理 RSS 2.0 格式
    ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
    for entry in root.findall(".//item"):
        if len(items) >= max_items:
            break

        title = _get_text(entry, "title")
        description = _get_text(entry, "description")
        link = _get_text(entry, "link")
        guid = _get_text(entry, "guid") or link
        author = _get_text(entry, "author")
        pub_date_str = _get_text(entry, "pubDate")
        content = _get_text(entry, "content:encoded", ns) or description
        categories = [cat.text for cat in entry.findall("category") if cat.text]

        # 如果 title 或 description 为空则跳过
        if not title and not description:
            continue

        # 关键词过滤
        if filter_keyword:
            text_to_check = (title or "").lower() + " " + (description or "").lower()
            if filter_keyword not in text_to_check:
                continue

        items.append({
            "title": title or "(No title)",
            "description": description or "",
            "link": link or "",
            "guid": guid or link or title,
            "pub_date": _parse_rss_date(pub_date_str) if pub_date_str else "",
            "author": author or "",
            "categories": categories or [],
            "content": content or "",
        })

    # 处理 Atom 格式 (如果没有找到 item 则尝试)
    if not items:
        ns_atom = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns_atom):
            if len(items) >= max_items:
                break

            title = _get_text(entry, "atom:title", ns_atom)
            link_el = entry.find("atom:link", ns_atom)
            link = link_el.get("href", "") if link_el is not None else ""
            summary = _get_text(entry, "atom:summary", ns_atom) or _get_text(entry, "atom:content", ns_atom)
            author_el = entry.find("atom:author", ns_atom)
            author = _get_text(author_el, "atom:name", ns_atom) if author_el is not None else ""
            published = _get_text(entry, "atom:published", ns_atom) or _get_text(entry, "atom:updated", ns_atom)
            entry_id = _get_text(entry, "atom:id", ns_atom) or link

            if filter_keyword:
                text_to_check = (title or "").lower() + " " + (summary or "").lower()
                if filter_keyword not in text_to_check:
                    continue

            items.append({
                "title": title or "(No title)",
                "description": summary or "",
                "link": link or "",
                "guid": entry_id or link or "",
                "pub_date": published or "",
                "author": author or "",
                "categories": [],
                "content": summary or "",
            })

    context["logger"]["info"](f"Got {len(items)} items from proxy")
    return items


def _get_text(element, tag, ns=None):
    """获取 XML 元素的文本内容。"""
    if ns:
        el = element.find(tag, ns)
    else:
        el = element.find(tag)
    return el.text if el is not None and el.text else ""


def _parse_rss_date(date_str: str) -> str:
    """解析 RSS 日期字符串为 ISO 格式。"""
    import datetime
    try:
        # RFC 2822 格式
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.isoformat()
    except Exception:
        return date_str
