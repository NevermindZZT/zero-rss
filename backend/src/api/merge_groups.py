"""合并源管理 API。

将多个脚本实例合并为一个 RSS 订阅源。
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import MergeGroup, MergeGroupItem, Instance, RSSItem
from ..schemas import MergeGroupCreate, MergeGroupUpdate, MergeGroupResponse
from ..auth import verify_token
from ..config import settings

logger = logging.getLogger("zero-rss.api.merge_groups")
router = APIRouter(prefix="/api/merge-groups", tags=["merge-groups"], dependencies=[Depends(verify_token)])


@router.get("", response_model=list[MergeGroupResponse])
async def list_merge_groups(
    db: AsyncSession = Depends(get_db),
):
    """获取所有合并源列表。"""
    result = await db.execute(
        select(MergeGroup).options(selectinload(MergeGroup.items).selectinload(MergeGroupItem.instance))
        .order_by(MergeGroup.updated_at.desc())
    )
    groups = result.scalars().all()
    return [_group_to_response(g) for g in groups]


@router.post("", response_model=MergeGroupResponse, status_code=201)
async def create_merge_group(
    data: MergeGroupCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建合并源。"""
    rss_token = str(uuid.uuid4()).replace("-", "")

    # 校验 slug（跨表查重由 _validate_slug 处理）
    from .instances import _validate_slug
    group = MergeGroup(
        name=data.name,
        description=data.description,
        rss_token=rss_token,
        rss_slug=await _validate_slug(data.rss_slug, db),
        max_items=data.max_items,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)

    # 添加实例成员
    for idx, inst_id in enumerate(data.instance_ids):
        item = MergeGroupItem(
            group_id=group.id,
            instance_id=inst_id,
            sort_order=idx,
        )
        db.add(item)

    await db.commit()

    # 重新读取
    result = await db.execute(
        select(MergeGroup).where(MergeGroup.id == group.id)
        .options(selectinload(MergeGroup.items).selectinload(MergeGroupItem.instance))
    )
    group = result.scalar_one()
    return _group_to_response(group)


@router.get("/{group_id}", response_model=MergeGroupResponse)
async def get_merge_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取合并源详情。"""
    result = await db.execute(
        select(MergeGroup).where(MergeGroup.id == group_id)
        .options(selectinload(MergeGroup.items).selectinload(MergeGroupItem.instance))
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Merge group not found")
    return _group_to_response(group)


@router.put("/{group_id}", response_model=MergeGroupResponse)
async def update_merge_group(
    group_id: str,
    data: MergeGroupUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新合并源配置。"""
    result = await db.execute(
        select(MergeGroup).where(MergeGroup.id == group_id)
        .options(selectinload(MergeGroup.items).selectinload(MergeGroupItem.instance))
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Merge group not found")

    if data.name is not None:
        group.name = data.name
    if data.description is not None:
        group.description = data.description
    if data.max_items is not None:
        group.max_items = data.max_items

    # 更新实例成员
    if data.rss_slug is not None:
        from .instances import _validate_slug
        group.rss_slug = await _validate_slug(
            data.rss_slug,
            db,
            exclude_merge_group_id=group_id,
        )

    if data.instance_ids is not None:
        await db.execute(
            sa_delete(MergeGroupItem.__table__).where(MergeGroupItem.group_id == group_id)
        )
        for idx, inst_id in enumerate(data.instance_ids):
            item = MergeGroupItem(
                group_id=group_id,
                instance_id=inst_id,
                sort_order=idx,
            )
            db.add(item)

    group.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # 重新读取
    result = await db.execute(
        select(MergeGroup).where(MergeGroup.id == group_id)
        .options(selectinload(MergeGroup.items).selectinload(MergeGroupItem.instance))
    )
    group = result.scalar_one()
    return _group_to_response(group)


@router.delete("/{group_id}", status_code=204)
async def delete_merge_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除合并源。"""
    group = await db.get(MergeGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Merge group not found")
    await db.delete(group)
    await db.commit()


def _group_to_response(group: MergeGroup) -> MergeGroupResponse:
    """将 MergeGroup ORM 模型转换为响应模型。"""
    instance_ids: list[str] = []
    instance_names: list[str] = []

    # 按 sort_order 排序
    sorted_items = sorted(group.items, key=lambda x: x.sort_order) if group.items else []
    for item in sorted_items:
        instance_ids.append(item.instance_id)
        if item.instance:
            instance_names.append(item.instance.name)

    slug_part = group.rss_slug if group.rss_slug else group.rss_token
    rss_url = f"{settings.base_url}/rss/merge/{slug_part}.xml"

    return MergeGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description or "",
        rss_token=group.rss_token,
        rss_slug=group.rss_slug,
        rss_url=rss_url,
        max_items=group.max_items or 100,
        instance_ids=instance_ids,
        instance_names=instance_names,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )
