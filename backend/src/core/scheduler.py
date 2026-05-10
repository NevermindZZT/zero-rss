"""任务调度器。

基于 APScheduler 实现，管理脚本实例的定时/间隔执行。
支持:
- interval: 每隔 N 分钟执行
- cron: 在指定时间点执行 (支持多时间点)
- on_refresh: 不注册定时任务, 由 RSS 请求端触发
- manual: 不注册定时任务, 仅手动触发
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from sqlalchemy import select, delete as sa_delete, func
from sqlalchemy.orm import selectinload

from ..database import async_session
from ..models import Instance, RunHistory, RSSItem
from ..config import settings
from .item_guid import build_item_guid

logger = logging.getLogger("zero-rss.scheduler")

# 全局调度器实例
scheduler: AsyncIOScheduler | None = None


def build_cron_trigger(expr: str) -> CronTrigger:
    """构建 CronTrigger。

    支持两种格式:
    - 5 位: 分 时 日 月 周 (标准 crontab)
    - 6 位: 秒 分 时 日 月 周
    """
    normalized = (expr or "").strip()
    parts = normalized.split()

    if len(parts) == 5:
        return CronTrigger.from_crontab(normalized)

    if len(parts) == 6:
        second, minute, hour, day, month, day_of_week = parts
        return CronTrigger(
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
        )

    raise ValueError("Cron expression must have 5 or 6 fields")


def get_scheduler() -> AsyncIOScheduler:
    """获取全局调度器实例。"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


async def execute_instance(instance_id: str):
    """执行指定实例的脚本。

    由 APScheduler 作业触发调用。分两步执行:
    1. 从数据库读取脚本信息和参数 (session 内)
    2. 执行脚本 (session 外, 避免 greenlet 冲突)
    3. 保存执行结果 (新 session)

    Args:
        instance_id: 实例 ID。
    """
    from .runner import run_script

    started_at = datetime.now(timezone.utc)

    # 第一步: 在 session 中读取脚本信息和参数
    async with async_session() as session:
        result = await session.execute(
            select(Instance).where(Instance.id == instance_id).options(selectinload(Instance.script))
        )
        instance = result.scalar_one_or_none()
        if not instance:
            logger.warning(f"Instance {instance_id} not found, skipping")
            return
        if not instance.enabled:
            logger.info(f"Instance {instance_id} is disabled, skipping")
            return

        script = instance.script
        if not script:
            logger.warning(f"Script for instance {instance_id} not found, skipping")
            return

        # 提取执行所需的数据
        script_code = script.code
        params = json.loads(instance.params) if isinstance(instance.params, str) else instance.params
        instance_name = instance.name
        script_name = script.name
        max_items = instance.max_items or 100

        # 创建运行历史记录
        history_id = str(uuid.uuid4())
        history = RunHistory(
            id=history_id,
            instance_id=instance_id,
            status="running",
            started_at=started_at,
        )
        session.add(history)
        await session.commit()

    logger.info(f"Executing instance: {instance_name} (script: {script_name})")

    # 第二步: 执行脚本 (在 session 外)
    try:
        items = await run_script(script_code, params, instance_id)
        completed_at = datetime.now(timezone.utc)
        duration = int((completed_at - started_at).total_seconds() * 1000)

        # 第三步: 在 session 中保存结果
        async with async_session() as session:
            inst = await session.get(Instance, instance_id)
            hist = await session.get(RunHistory, history_id)
            if hist is None:
                logger.error(f"RunHistory {history_id} not found")
                return

            hist.status = "success"
            hist.items_count = len(items)
            hist.duration_ms = duration
            hist.completed_at = completed_at

            if inst:
                inst.last_run_at = completed_at
                inst.last_run_status = "success"
                inst.last_error = None

            # 保留最近 50 条历史记录
            subq = (
                select(RunHistory.id)
                .where(RunHistory.instance_id == instance_id)
                .order_by(RunHistory.started_at.desc())
                .offset(49)
                .limit(1)
            )
            subq_result = await session.execute(subq)
            oldest_allowed = subq_result.scalar_one_or_none()
            if oldest_allowed:
                await session.execute(
                    sa_delete(RunHistory.__table__)
                    .where(RunHistory.instance_id == instance_id)
                    .where(RunHistory.started_at < (
                        select(RunHistory.started_at)
                        .where(RunHistory.id == oldest_allowed)
                    ).scalar_subquery())
                )

            # 更新 RSS 条目
            await session.execute(
                sa_delete(RSSItem.__table__).where(RSSItem.instance_id == instance_id)
            )

            for item in items[:max_items]:
                pub_date = None
                if item.get("pub_date"):
                    try:
                        pub_date = datetime.fromisoformat(item["pub_date"].replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pub_date = None

                rss_item = RSSItem(
                    instance_id=instance_id,
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

            await session.commit()

        logger.info(f"Instance {instance_name} executed successfully, {len(items)} items")

    except Exception as e:
        completed_at = datetime.now(timezone.utc)
        duration = int((completed_at - started_at).total_seconds() * 1000)

        # 在 session 中记录错误
        async with async_session() as session:
            hist = await session.get(RunHistory, history_id)
            inst = await session.get(Instance, instance_id)

            if hist:
                hist.status = "error"
                hist.error_message = str(e)
                hist.duration_ms = duration
                hist.completed_at = completed_at

            if inst:
                inst.last_run_status = "error"
                inst.last_error = str(e)

            await session.commit()

        logger.error(f"Instance {instance_name} execution failed: {e}")


async def register_instance_jobs(instance_id: str | None = None):
    """注册实例的定时任务。

    对 interval 和 cron 类型的实例创建 APScheduler 作业。
    对 on_refresh 和 manual 类型不创建定时任务。

    Args:
        instance_id: 如果提供，只注册该实例；否则注册所有已启用的实例。
    """
    sched = get_scheduler()

    async with async_session() as session:
        stmt = select(Instance).where(Instance.enabled == True).options(selectinload(Instance.script))  # noqa: E712

        if instance_id:
            stmt = stmt.where(Instance.id == instance_id)

        result = await session.execute(stmt)
        instances = result.scalars().all()

        for instance in instances:
            # 清除该实例已有的所有作业
            job_id_prefix = f"instance_{instance.id}"
            for job in sched.get_jobs():
                if job.id.startswith(job_id_prefix):
                    job.remove()

            schedule_type = instance.schedule_type or "interval"
            schedule_config = {}
            if instance.schedule_config:
                try:
                    schedule_config = json.loads(instance.schedule_config) if isinstance(instance.schedule_config, str) else instance.schedule_config
                except (json.JSONDecodeError, TypeError):
                    schedule_config = {}

            if schedule_type == "interval":
                interval_minutes = schedule_config.get("interval_minutes", 60)
                trigger = IntervalTrigger(minutes=interval_minutes)
                sched.add_job(
                    execute_instance,
                    trigger,
                    args=[instance.id],
                    id=f"{job_id_prefix}_interval",
                    replace_existing=True,
                    name=f"Interval: {instance.name}",
                )
                logger.info(f"Registered interval job for {instance.name} (every {interval_minutes} min)")

            elif schedule_type == "cron":
                cron_exprs = schedule_config.get("cron_expressions", [])
                for idx, expr in enumerate(cron_exprs):
                    try:
                        trigger = build_cron_trigger(expr)
                        sched.add_job(
                            execute_instance,
                            trigger,
                            args=[instance.id],
                            id=f"{job_id_prefix}_cron_{idx}",
                            replace_existing=True,
                            name=f"Cron[{idx}]: {instance.name} ({expr})",
                        )
                        logger.info(f"Registered cron job for {instance.name} ({expr})")
                    except (ValueError, Exception) as e:
                        logger.warning(f"Invalid cron expression '{expr}' for {instance.name}: {e}")

            # on_refresh 和 manual 不注册定时任务
            elif schedule_type == "on_refresh":
                logger.info(f"Instance {instance.name} uses on_refresh trigger, no scheduled job")
            elif schedule_type == "manual":
                logger.info(f"Instance {instance.name} uses manual trigger, no scheduled job")


async def remove_instance_jobs(instance_id: str):
    """移除指定实例的所有已注册作业。

    Args:
        instance_id: 实例 ID。
    """
    sched = get_scheduler()
    job_id_prefix = f"instance_{instance_id}"
    for job in sched.get_jobs():
        if job.id.startswith(job_id_prefix):
            job.remove()
            logger.info(f"Removed job {job.id} for instance {instance_id}")


async def start_scheduler():
    """启动调度器并注册所有已启用的实例任务。"""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        logger.info("Scheduler started")
        await register_instance_jobs()
        logger.info("All instance jobs registered")


async def stop_scheduler():
    """停止调度器。"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("Scheduler stopped")
