"""系统管理 API。"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Script, Instance, RSSItem, RunHistory, MergeGroup
from ..schemas import SystemStats, AuthRequest, AuthResponse
from ..config import settings
from ..auth import verify_token

logger = logging.getLogger("zero-rss.api.system")
router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def health_check():
    """健康检查端点 (无需认证)。"""
    return {"status": "ok", "version": settings.app_version}


@router.post("/auth", response_model=AuthResponse)
async def auth_login(data: AuthRequest):
    """验证 Token。"""
    if data.token == settings.auth_token:
        return AuthResponse(success=True, message="Authentication successful")
    raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/stats", response_model=SystemStats, dependencies=[Depends(verify_token)])
async def system_stats(db: AsyncSession = Depends(get_db)):
    """获取系统统计信息。"""
    total_scripts = (await db.execute(select(func.count(Script.id)))).scalar() or 0
    total_instances = (await db.execute(select(func.count(Instance.id)))).scalar() or 0
    total_items = (await db.execute(select(func.count(RSSItem.id)))).scalar() or 0
    enabled_instances = (
        await db.execute(
            select(func.count(Instance.id)).where(Instance.enabled == True)  # noqa: E712
        )
    ).scalar() or 0
    recent_errors = (
        await db.execute(
            select(func.count(RunHistory.id))
            .where(RunHistory.status == "error")
        )
    ).scalar() or 0
    total_merge_groups = (await db.execute(select(func.count(MergeGroup.id)))).scalar() or 0

    return SystemStats(
        total_scripts=total_scripts,
        total_instances=total_instances,
        total_items=total_items,
        enabled_instances=enabled_instances,
        recent_errors=recent_errors,
        total_merge_groups=total_merge_groups,
    )
