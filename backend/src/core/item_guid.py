"""RSS 条目 GUID 生成工具。"""

import hashlib
import json
from typing import Any


def build_item_guid(item: dict[str, Any]) -> str:
    """根据条目内容生成稳定 GUID。

    规则:
    - base: 优先使用用户提供 guid，其次 link，再次 title，最后使用固定占位。
    - digest: 由会影响读者看到内容的字段计算哈希。
    - 最终 GUID: "{base}#{digest16}"，内容变化时 GUID 变化。
    """
    base = str(item.get("guid") or item.get("link") or item.get("title") or "item")

    fingerprint = {
        "title": item.get("title") or "",
        "description": item.get("description") or "",
        "content": item.get("content") or "",
        "link": item.get("link") or "",
        "author": item.get("author") or "",
        "pub_date": item.get("pub_date") or "",
        "categories": item.get("categories") or [],
        "image": item.get("image") or "",
    }
    raw = json.dumps(fingerprint, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    return f"{base}#{digest}"
