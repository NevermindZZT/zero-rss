"""RSS XML 生成器。

使用 feedgen 库从数据库条目生成标准 RSS 2.0 XML。
支持刷新触发逻辑: 如果实例配置了 on_refresh 且数据过期, 则先更新数据再生成。
"""

import json
import logging
from datetime import datetime, timezone, timedelta

from feedgen.feed import FeedGenerator
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.orm import selectinload

from ..database import async_session
from ..models import Instance, RSSItem
from .item_guid import build_item_guid

logger = logging.getLogger("zero-rss.rss_generator")


async def generate_rss_xml(token: str, base_url: str = "") -> str | None:
    """根据 RSS Token 或 Slug 生成 RSS XML。

    先按 slug 查找实例, 未命中再按 token 查找。
    如果实例配置了 on_refresh 调度类型, 且数据已过期,
    则会先同步执行脚本更新数据再生成 XML。

    Args:
        token: RSS 订阅 token 或自定义 slug。
        base_url: 基础 URL, 用于生成 RSS 中的链接。

    Returns:
        RSS XML 字符串, 如果未找到则返回 None。
    """
    from .runner import run_script

    async with async_session() as session:
        # 先按 slug 查, 再按 token 查
        result = await session.execute(
            select(Instance).where(Instance.rss_slug == token).options(selectinload(Instance.script))
        )
        instance = result.scalar_one_or_none()
        if instance is None:
            result = await session.execute(
                select(Instance).where(Instance.rss_token == token).options(selectinload(Instance.script))
            )
            instance = result.scalar_one_or_none()
        if not instance:
            return None

        script = instance.script
        if not script:
            return None

        should_update = False

        # 检查是否需要刷新触发
        if instance.schedule_type == "on_refresh" and instance.enabled:
            schedule_config = {}
            if instance.schedule_config:
                try:
                    schedule_config = json.loads(instance.schedule_config) if isinstance(instance.schedule_config, str) else instance.schedule_config
                except (json.JSONDecodeError, TypeError):
                    schedule_config = {}

            refresh_interval = schedule_config.get("refresh_interval_minutes", 30)
            now = datetime.now(timezone.utc)
            last_run = instance.last_run_at

            if last_run is None:
                should_update = True
            else:
                # 确保 last_run 有时区信息
                if last_run.tzinfo is None:
                    last_run = last_run.replace(tzinfo=timezone.utc)
                if (now - last_run) > timedelta(minutes=refresh_interval):
                    should_update = True

        # 执行刷新触发更新
        if should_update:
            try:
                params = json.loads(instance.params) if isinstance(instance.params, str) else instance.params
                logger.info(f"On-refresh trigger: executing {instance.name}")
                items = await run_script(script.code, params, instance.id)

                # 更新条目
                from sqlalchemy import delete as sa_delete
                await session.execute(
                    sa_delete(RSSItem.__table__).where(RSSItem.instance_id == instance.id)
                )

                max_items = instance.max_items or 100
                for item in items[:max_items]:
                    pub_date = None
                    if item.get("pub_date"):
                        try:
                            pub_date = datetime.fromisoformat(item["pub_date"].replace("Z", "+00:00"))
                        except (ValueError, AttributeError):
                            pub_date = None

                    rss_item = RSSItem(
                        instance_id=instance.id,
                        guid=build_item_guid(item),
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        link=item.get("link", ""),
                        author=item.get("author", ""),
                        categories=json.dumps(item.get("categories", []), ensure_ascii=False),
                        content=item.get("content", ""),
                        image=item.get("image", ""),
                        pub_date=pub_date,
                    )
                    session.add(rss_item)

                instance.last_run_at = datetime.now(timezone.utc)
                instance.last_run_status = "success"
                instance.last_error = None
                await session.commit()
                logger.info(f"On-refresh update completed for {instance.name}, {len(items)} items")
            except Exception as e:
                logger.error(f"On-refresh update failed for {instance.name}: {e}")
                # 失败时使用旧数据继续生成 RSS

        # 从数据库查询条目
        items_result = await session.execute(
            select(RSSItem)
            .where(RSSItem.instance_id == instance.id)
            .order_by(RSSItem.pub_date.desc().nullslast(), RSSItem.created_at.desc())
            .limit(instance.max_items or 100)
        )
        items_query = items_result.scalars().all()

        # 构建 RSS Feed
        fg = FeedGenerator()
        fg.id(f"{base_url}/rss/{token}.xml")
        fg.title(instance.name)
        fg.description(instance.description or f"RSS feed for {instance.name}")
        fg.link(href=base_url or f"/rss/{token}.xml", rel="alternate")
        fg.language("zh-CN")

        if instance.last_run_at:
            fg.lastBuildDate(instance.last_run_at.strftime("%a, %d %b %Y %H:%M:%S +0000"))

        for item in items_query:
            fe = fg.add_entry()
            fe.id(item.guid or item.id)
            fe.title(item.title or "(No title)")
            # 优先输出 content，避免客户端只能看到旧摘要而错过正文更新
            entry_body = item.content or item.description or ""
            fe.description(entry_body)
            fe.link(href=item.link or "")

            if item.author:
                fe.author(name=item.author)
            pub_dt = item.pub_date or item.created_at
            if pub_dt:
                fe.pubDate(pub_dt.strftime("%a, %d %b %Y %H:%M:%S +0000"))
            if item.categories:
                try:
                    cats = json.loads(item.categories) if isinstance(item.categories, str) else item.categories
                    for cat in cats:
                        fe.category(term=cat)
                except (json.JSONDecodeError, TypeError):
                    pass

        return fg.rss_str(pretty=True).decode("utf-8")


async def generate_merged_rss_xml(token: str, base_url: str = "") -> str | None:
    """根据合并源 Token 或 Slug 生成合并 RSS XML。

    将多个实例的 RSS 条目合并到一个 Feed 中，
    按发布时间倒序排列。

    Args:
        token: 合并源的 RSS token 或自定义 slug。
        base_url: 基础 URL。

    Returns:
        RSS XML 字符串, 如果未找到则返回 None。
    """
    from ..models import MergeGroup, MergeGroupItem

    async with async_session() as session:
        # 先按 slug 查, 再按 token 查
        result = await session.execute(
            select(MergeGroup).where(MergeGroup.rss_slug == token)
            .options(selectinload(MergeGroup.items).selectinload(MergeGroupItem.instance))
        )
        group = result.scalar_one_or_none()
        if group is None:
            result = await session.execute(
                select(MergeGroup).where(MergeGroup.rss_token == token)
                .options(selectinload(MergeGroup.items).selectinload(MergeGroupItem.instance))
            )
            group = result.scalar_one_or_none()
        if not group:
            return None

        # 收集所有实例 ID
        instance_ids = [item.instance_id for item in group.items]

        if not instance_ids:
            # 空组, 返回空 feed
            fg = FeedGenerator()
            fg.id(f"{base_url}/rss/merge/{token}.xml")
            fg.title(group.name)
            fg.description(group.description or f"Merged RSS feed: {group.name}")
            fg.link(href=base_url or f"/rss/merge/{token}.xml", rel="alternate")
            fg.language("zh-CN")
            return fg.rss_str(pretty=True).decode("utf-8")

        # 查询所有实例的条目, 按时间倒序排列
        items_result = await session.execute(
            select(RSSItem)
            .where(RSSItem.instance_id.in_(instance_ids))
            .order_by(RSSItem.pub_date.desc().nullslast(), RSSItem.created_at.desc())
            .limit(group.max_items or 100)
        )
        all_items = items_result.scalars().all()

        # 构建 RSS Feed
        fg = FeedGenerator()
        fg.id(f"{base_url}/rss/merge/{token}.xml")
        fg.title(group.name)
        fg.description(group.description or f"Merged RSS feed: {group.name}")
        fg.link(href=base_url or f"/rss/merge/{token}.xml", rel="alternate")
        fg.language("zh-CN")

        # 获取实例名称映射
        instance_names = {}
        for item in group.items:
            if item.instance:
                instance_names[item.instance_id] = item.instance.name

        for item in all_items:
            fe = fg.add_entry()
            fe.id(item.guid or item.id)
            fe.title(item.title or "(No title)")
            # 合并源同样优先输出 content，保证客户端看到最新主体
            entry_body = item.content or item.description or ""
            fe.description(entry_body)
            fe.link(href=item.link or "")

            if item.author:
                fe.author(name=item.author)
            pub_dt = item.pub_date or item.created_at
            if pub_dt:
                fe.pubDate(pub_dt.strftime("%a, %d %b %Y %H:%M:%S +0000"))

            # 添加来源标签
            inst_name = instance_names.get(item.instance_id, "")
            if inst_name:
                fe.category(term=inst_name)

            if item.categories:
                try:
                    cats = json.loads(item.categories) if isinstance(item.categories, str) else item.categories
                    for cat in cats:
                        fe.category(term=cat)
                except (json.JSONDecodeError, TypeError):
                    pass

        return fg.rss_str(pretty=True).decode("utf-8")
