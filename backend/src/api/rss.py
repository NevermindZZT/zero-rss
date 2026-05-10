"""RSS 订阅源公开端点。"""

import hashlib
import logging
from datetime import timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from ..core.rss_generator import generate_rss_xml, generate_merged_rss_xml

logger = logging.getLogger("zero-rss.api.rss")
router = APIRouter(tags=["rss"])


def _rfc2822(dt) -> str:
    """格式化 datetime 为 RFC 2822 字符串用于 HTTP 头。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # HTTP headers require GMT, not +0000
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


async def _build_rss_response(
    xml_result: tuple | str | None,
    if_modified_since: str | None = None,
    if_none_match: str | None = None,
):
    """构建带条件 GET 支持的 RSS 响应。

    Args:
        xml_result: generate_rss_xml 的返回值（str 或 (str, datetime) 或 None）。
        if_modified_since: If-Modified-Since 请求头值。
        if_none_match: If-None-Match 请求头值。
    """
    if xml_result is None:
        raise HTTPException(status_code=404, detail="RSS feed not found")

    if isinstance(xml_result, tuple):
        rss_xml, last_modified = xml_result
    else:
        rss_xml, last_modified = xml_result, None

    # 计算 ETag (内容哈希)
    etag = hashlib.md5(rss_xml.encode("utf-8")).hexdigest()

    # 条件 GET: ETag 匹配 → 304
    if if_none_match and if_none_match.strip('"') == etag:
        return Response(status_code=304)

    headers = {
        "Cache-Control": "no-cache, must-revalidate",
        "ETag": f'"{etag}"',
    }

    # 条件 GET: Last-Modified 匹配 → 304
    if last_modified is not None:
        last_mod_str = _rfc2822(last_modified)
        headers["Last-Modified"] = last_mod_str
        if if_modified_since and if_modified_since == last_mod_str:
            return Response(status_code=304)

    return Response(
        content=rss_xml,
        media_type="application/rss+xml; charset=utf-8",
        headers=headers,
    )


@router.get("/rss/{token}.xml")
async def get_rss_feed(token: str, request: Request):
    """获取单个实例的 RSS 订阅源 XML。

    公开端点，无需认证。
    如果实例配置了 on_refresh 调度且数据过期，会自动触发更新再返回。
    支持条件 GET (If-Modified-Since / If-None-Match)。
    """
    base_url = str(request.base_url).rstrip("/")
    result = await generate_rss_xml(token, base_url=base_url)

    return await _build_rss_response(
        result,
        if_modified_since=request.headers.get("if-modified-since"),
        if_none_match=request.headers.get("if-none-match"),
    )


@router.get("/rss/merge/{token}.xml")
async def get_merged_rss_feed(token: str, request: Request):
    """获取合并源的 RSS 订阅源 XML。

    将多个实例的条目合并到一个 RSS Feed 中，
    按发布时间倒序排列。
    公开端点，无需认证。
    支持条件 GET (If-Modified-Since / If-None-Match)。
    """
    base_url = str(request.base_url).rstrip("/")
    result = await generate_merged_rss_xml(token, base_url=base_url)

    return await _build_rss_response(
        result,
        if_modified_since=request.headers.get("if-modified-since"),
        if_none_match=request.headers.get("if-none-match"),
    )
