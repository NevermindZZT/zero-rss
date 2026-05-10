"""脚本实例管理 API。"""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Instance, Script, RSSItem, RunHistory
from ..schemas import (
    InstanceCreate, InstanceUpdate, InstanceResponse,
    RSSItemResponse, RunHistoryResponse, PaginatedResponse,
)
from ..auth import verify_token
from ..core.scheduler import register_instance_jobs, remove_instance_jobs
from ..core.runner import run_script, test_script, ScriptError
from ..config import settings

logger = logging.getLogger("zero-rss.api.instances")
router = APIRouter(prefix="/api/instances", tags=["instances"], dependencies=[Depends(verify_token)])


@router.get("", response_model=list[InstanceResponse])
async def list_instances(
    script_id: str = "",
    search: str = "",
    db: AsyncSession = Depends(get_db),
):
    """获取所有脚本实例列表。"""
    query = (
        select(Instance)
        .options(selectinload(Instance.script))
        .order_by(Instance.updated_at.desc())
    )

    if script_id:
        query = query.where(Instance.script_id == script_id)
    if search:
        query = query.where(Instance.name.ilike(f"%{search}%"))

    result = await db.execute(query)
    instances = result.scalars().all()

    items = []
    for inst in instances:
        items.append(_instance_to_response(inst))

    return items


@router.post("", response_model=InstanceResponse, status_code=201)
async def create_instance(
    data: InstanceCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新的脚本实例。

    实例 = 脚本模板 + 具体参数配置 + 调度策略。
    每个实例有唯一 RSS Token, 生成独立的 RSS 订阅源。
    """
    # 验证脚本存在
    script = await db.get(Script, data.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # 生成唯一 RSS Token
    rss_token = str(uuid.uuid4()).replace("-", "")

    instance = Instance(
        script_id=data.script_id,
        name=data.name,
        description=data.description,
        params=json.dumps(data.params, ensure_ascii=False),
        schedule_type=data.schedule_type,
        schedule_config=json.dumps(data.schedule_config) if data.schedule_config else None,
        rss_token=rss_token,
        max_items=data.max_items,
    )
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    await db.refresh(instance, ["script"])

    # 注册调度任务
    await register_instance_jobs(instance.id)

    return _instance_to_response(instance)


@router.get("/{instance_id}", response_model=InstanceResponse)
async def get_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单个实例详情。"""
    result = await db.execute(
        select(Instance)
        .options(selectinload(Instance.script))
        .where(Instance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    return _instance_to_response(instance)


@router.put("/{instance_id}", response_model=InstanceResponse)
async def update_instance(
    instance_id: str,
    data: InstanceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新实例配置。"""
    result = await db.execute(
        select(Instance)
        .options(selectinload(Instance.script))
        .where(Instance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    update_data = data.model_dump(exclude_unset=True)
    if "params" in update_data and update_data["params"] is not None:
        update_data["params"] = json.dumps(update_data["params"], ensure_ascii=False)
    if "schedule_config" in update_data and update_data["schedule_config"] is not None:
        update_data["schedule_config"] = json.dumps(update_data["schedule_config"], ensure_ascii=False)
    if "enabled" in update_data:
        update_data["enabled"] = 1 if update_data["enabled"] else 0

    for key, value in update_data.items():
        setattr(instance, key, value)

    instance.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(instance, ["script"])

    # 重新注册调度任务
    await remove_instance_jobs(instance.id)
    await register_instance_jobs(instance.id)

    return _instance_to_response(instance)


@router.delete("/{instance_id}", status_code=204)
async def delete_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除实例。"""
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    # 移除调度任务
    await remove_instance_jobs(instance.id)

    await db.delete(instance)
    await db.commit()


@router.post("/{instance_id}/run")
async def run_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    """手动触发实例运行。"""
    result = await db.execute(
        select(Instance)
        .options(selectinload(Instance.script))
        .where(Instance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    from ..core.scheduler import execute_instance
    try:
        await execute_instance(instance_id)
        return {"status": "success", "message": f"Instance {instance.name} executed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/test")
async def test_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    """测试运行实例 (返回结果但不保存到数据库)。"""
    result = await db.execute(
        select(Instance)
        .options(selectinload(Instance.script))
        .where(Instance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    params = json.loads(instance.params) if isinstance(instance.params, str) else instance.params

    try:
        items = await test_script(instance.script.code, params)
        return {"status": "success", "items_count": len(items), "items": items}
    except ScriptError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/{instance_id}/history", response_model=PaginatedResponse)
async def get_instance_history(
    instance_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取实例的运行历史。"""
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    query = (
        select(RunHistory)
        .where(RunHistory.instance_id == instance_id)
        .order_by(RunHistory.started_at.desc())
    )

    total_result = await db.execute(
        select(func.count(RunHistory.id)).where(RunHistory.instance_id == instance_id)
    )
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    records = result.scalars().all()

    items = []
    for r in records:
        items.append(RunHistoryResponse(
            id=r.id,
            instance_id=r.instance_id,
            status=r.status,
            items_count=r.items_count,
            error_message=r.error_message,
            duration_ms=r.duration_ms,
            started_at=r.started_at,
            completed_at=r.completed_at,
        ))

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{instance_id}/items", response_model=PaginatedResponse)
async def get_instance_items(
    instance_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取实例的 RSS 条目列表。"""
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    query = (
        select(RSSItem)
        .where(RSSItem.instance_id == instance_id)
        .order_by(RSSItem.pub_date.desc().nullslast(), RSSItem.created_at.desc())
    )

    total_result = await db.execute(
        select(func.count(RSSItem.id)).where(RSSItem.instance_id == instance_id)
    )
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    records = result.scalars().all()

    items = []
    for item in records:
        categories = []
        if item.categories:
            try:
                categories = json.loads(item.categories) if isinstance(item.categories, str) else item.categories
            except (json.JSONDecodeError, TypeError):
                categories = []

        items.append(RSSItemResponse(
            id=item.id,
            guid=item.guid,
            title=item.title,
            description=item.description,
            link=item.link,
            author=item.author,
            categories=categories,
            content=item.content,
            image=item.image,
            pub_date=item.pub_date,
            created_at=item.created_at,
        ))

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


def _instance_to_response(instance: Instance) -> InstanceResponse:
    """将 Instance ORM 模型转换为响应模型。"""
    params = {}
    if instance.params:
        try:
            params = json.loads(instance.params) if isinstance(instance.params, str) else instance.params
        except (json.JSONDecodeError, TypeError):
            params = {}

    schedule_config = None
    if instance.schedule_config:
        try:
            schedule_config = json.loads(instance.schedule_config) if isinstance(instance.schedule_config, str) else instance.schedule_config
        except (json.JSONDecodeError, TypeError):
            schedule_config = None

    script_name = instance.script.name if instance.script else ""

    rss_url = f"{settings.base_url}/rss/{instance.rss_token}.xml"

    return InstanceResponse(
        id=instance.id,
        script_id=instance.script_id,
        script_name=script_name,
        name=instance.name,
        description=instance.description or "",
        params=params,
        schedule_type=instance.schedule_type or "interval",
        schedule_config=schedule_config,
        rss_token=instance.rss_token,
        rss_url=rss_url,
        enabled=bool(instance.enabled),
        max_items=instance.max_items or 100,
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        last_run_at=instance.last_run_at,
        last_run_status=instance.last_run_status,
        last_error=instance.last_error,
    )
