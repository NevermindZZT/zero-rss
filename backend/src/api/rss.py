"""RSS 订阅源公开端点。"""

import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from ..core.rss_generator import generate_rss_xml, generate_merged_rss_xml

logger = logging.getLogger("zero-rss.api.rss")
router = APIRouter(tags=["rss"])


@router.get("/rss/{token}.xml")
async def get_rss_feed(token: str, request: Request):
    """获取单个实例的 RSS 订阅源 XML。

    公开端点，无需认证。
    如果实例配置了 on_refresh 调度且数据过期，会自动触发更新再返回。
    """
    base_url = str(request.base_url).rstrip("/")
    rss_xml = await generate_rss_xml(token, base_url=base_url)

    if rss_xml is None:
        raise HTTPException(status_code=404, detail="RSS feed not found")

    return Response(
        content=rss_xml,
        media_type="application/rss+xml; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


@router.get("/rss/merge/{token}.xml")
async def get_merged_rss_feed(token: str, request: Request):
    """获取合并源的 RSS 订阅源 XML。

    将多个实例的条目合并到一个 RSS Feed 中，
    按发布时间倒序排列。
    公开端点，无需认证。
    """
    base_url = str(request.base_url).rstrip("/")
    rss_xml = await generate_merged_rss_xml(token, base_url=base_url)

    if rss_xml is None:
        raise HTTPException(status_code=404, detail="Merged RSS feed not found")

    return Response(
        content=rss_xml,
        media_type="application/rss+xml; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
