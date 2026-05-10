"""
zero-rss 示例脚本: GitHub Releases

获取指定 GitHub 仓库的最新 Releases。

配置参数:
- owner: 仓库所有者
- repo: 仓库名
"""

NAME = "GitHub Releases"
DESCRIPTION = "获取指定 GitHub 仓库的最新 Releases 信息"
VERSION = "1.0.0"
AUTHOR = "zero-rss"

PARAMS = [
    {
        "name": "owner",
        "label": "仓库所有者",
        "type": "string",
        "required": True,
        "description": "GitHub 仓库所有者用户名",
        "default": "",
    },
    {
        "name": "repo",
        "label": "仓库名",
        "type": "string",
        "required": True,
        "description": "GitHub 仓库名称",
        "default": "",
    },
    {
        "name": "max_releases",
        "label": "最大数量",
        "type": "number",
        "required": False,
        "description": "获取的最大 Release 数量",
        "default": 10,
    },
]

SCHEDULE = {
    "type": "interval",
    "interval_minutes": 60,
}


async def run(params, context):
    """获取 GitHub 仓库 Releases 并返回 RSS 条目列表。"""
    import httpx

    owner = params.get("owner", "").strip()
    repo = params.get("repo", "").strip()
    max_releases = int(params.get("max_releases", 10))

    if not owner or not repo:
        raise ValueError("owner 和 repo 不能为空")

    url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page={max_releases}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    context["logger"]["info"](f"Fetching releases from {url}")

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        releases = response.json()

    items = []
    for release in releases:
        tag_name = release.get("tag_name", "")
        html_url = release.get("html_url", "")
        body = release.get("body", "") or ""
        published_at = release.get("published_at", "")
        author_name = release.get("author", {}).get("login", "")

        # 截断过长内容
        if len(body) > 500:
            body = body[:500] + "..."

        items.append({
            "title": f"{repo} {tag_name}",
            "description": body,
            "link": html_url,
            "guid": html_url,
            "pub_date": published_at,
            "author": author_name,
            "categories": [f"release", f"{owner}/{repo}"],
        })

    context["logger"]["info"](f"Got {len(items)} releases")
    return items
