"""
zero-rss 示例脚本: Hacker News 热门

获取 Hacker News 热门文章。
"""

NAME = "Hacker News"
DESCRIPTION = "获取 Hacker News 最新热门文章"
VERSION = "1.0.0"
AUTHOR = "zero-rss"

PARAMS = [
    {
        "name": "count",
        "label": "文章数量",
        "type": "number",
        "required": False,
        "description": "获取的文章数量",
        "default": 20,
    },
    {
        "name": "type",
        "label": "类型",
        "type": "select",
        "required": False,
        "description": "文章类型",
        "default": "top",
        "options": [
            {"label": "热门 (Top)", "value": "top"},
            {"label": "最新 (New)", "value": "new"},
            {"label": "最佳 (Best)", "value": "best"},
        ],
    },
]

SCHEDULE = {
    "type": "interval",
    "interval_minutes": 30,
}


async def run(params, context):
    """获取 Hacker News 文章并返回 RSS 条目列表。"""
    import httpx

    count = int(params.get("count", 20))
    story_type = params.get("type", "top")

    base_url = "https://hacker-news.firebaseio.com/v0"
    type_map = {
        "top": f"{base_url}/topstories.json",
        "new": f"{base_url}/newstories.json",
        "best": f"{base_url}/beststories.json",
    }

    story_ids_url = type_map.get(story_type, type_map["top"])
    context["logger"]["info"](f"Fetching {story_type} stories from HN")

    async with httpx.AsyncClient() as client:
        resp = await client.get(story_ids_url, timeout=30)
        resp.raise_for_status()
        story_ids = resp.json()[:count]

        items = []
        for story_id in story_ids:
            story_url = f"{base_url}/item/{story_id}.json"
            try:
                story_resp = await client.get(story_url, timeout=15)
                story_resp.raise_for_status()
                story = story_resp.json()
                if not story or story.get("type") != "story" or story.get("title") is None:
                    continue

                title = story.get("title", "")
                link = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                description = story.get("text", "") or ""
                author = story.get("by", "")
                score = story.get("score", 0)
                time_ts = story.get("time", 0)

                import datetime
                pub_date = datetime.datetime.fromtimestamp(time_ts, tz=datetime.timezone.utc).isoformat() if time_ts else ""

                if len(description) > 300:
                    description = description[:300] + "..."

                items.append({
                    "title": f"[{score}★] {title}",
                    "description": description or f"Hacker News 文章，得分: {score}",
                    "link": link,
                    "guid": str(story_id),
                    "pub_date": pub_date,
                    "author": author,
                    "categories": ["hacker-news", story_type],
                })
            except Exception:
                continue

    context["logger"]["info"](f"Got {len(items)} HN stories")
    return items
