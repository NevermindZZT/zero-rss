"""Pydantic 请求/响应模型。"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ─── 脚本模板 ───


class ScriptCreate(BaseModel):
    """上传/创建脚本请求。"""
    code: str = Field(..., description="Python 脚本源代码")


class ScriptUpdate(BaseModel):
    """更新脚本请求。"""
    code: str = Field(..., description="Python 脚本源代码")


class ScriptResponse(BaseModel):
    """脚本模板响应。"""
    id: str
    name: str
    description: str
    version: str
    author: str
    filename: str
    params_schema: list[dict[str, Any]] = []
    code: str = ""
    default_schedule: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ScriptListItem(BaseModel):
    """脚本模板列表项 (不含代码内容)。"""
    id: str
    name: str
    description: str
    version: str
    author: str
    filename: str
    params_schema: list[dict[str, Any]] = []
    default_schedule: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    instance_count: int = 0

    class Config:
        from_attributes = True


# ─── 脚本实例 ───


class InstanceCreate(BaseModel):
    """创建实例请求。"""
    script_id: str = Field(..., description="脚本模板 ID")
    name: str = Field(..., description="实例名称")
    description: str = Field(default="", description="实例描述")
    params: dict[str, Any] = Field(default_factory=dict, description="参数配置")
    schedule_type: str = Field(default="interval", description="调度类型: interval, cron, on_refresh, manual")
    schedule_config: dict[str, Any] | None = Field(default=None, description="调度配置")
    rss_slug: str | None = Field(default=None, description="自定义 RSS 路径别名, 如 my-feed")
    max_items: int = Field(default=100, description="RSS 最大条目数")


class InstanceUpdate(BaseModel):
    """更新实例请求。"""
    name: str | None = None
    description: str | None = None
    params: dict[str, Any] | None = None
    schedule_type: str | None = None
    schedule_config: dict[str, Any] | None = None
    rss_slug: str | None = Field(default=None, description="自定义 RSS 路径别名, 如 my-feed")
    max_items: int | None = None
    enabled: bool | None = None


class InstanceResponse(BaseModel):
    """脚本实例响应。"""
    id: str
    script_id: str
    script_name: str = ""
    name: str
    description: str
    params: dict[str, Any] = {}
    schedule_type: str
    schedule_config: dict[str, Any] | None = None
    rss_token: str
    rss_slug: str | None = None
    rss_url: str = ""
    enabled: bool
    max_items: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_run_at: datetime | None = None
    last_run_status: str | None = None
    last_error: str | None = None

    class Config:
        from_attributes = True


# ─── RSS 条目 ───


class RSSItemResponse(BaseModel):
    """RSS 条目响应。"""
    id: str
    guid: str
    title: str
    description: str
    link: str
    author: str
    categories: list[str] = []
    content: str = ""
    image: str = ""
    pub_date: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ─── 运行历史 ───


class RunHistoryResponse(BaseModel):
    """运行历史响应。"""
    id: str
    instance_id: str
    status: str
    items_count: int
    error_message: str | None = None
    duration_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


# ─── 系统 ───


class SystemStats(BaseModel):
    """系统统计。"""
    total_scripts: int = 0
    total_instances: int = 0
    total_items: int = 0
    enabled_instances: int = 0
    recent_errors: int = 0
    total_merge_groups: int = 0


class AuthRequest(BaseModel):
    """认证请求。"""
    token: str = Field(..., description="访问 Token")


class AuthResponse(BaseModel):
    """认证响应。"""
    success: bool
    message: str = ""


# ─── 分页 ───


class PaginatedResponse(BaseModel):
    """分页响应包装。"""
    items: list[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


# ─── 合并源 ───


class MergeGroupCreate(BaseModel):
    """创建合并源请求。"""
    name: str = Field(..., description="合并源名称")
    description: str = Field(default="", description="描述")
    instance_ids: list[str] = Field(default_factory=list, description="包含的实例 ID 列表")
    rss_slug: str | None = Field(default=None, description="自定义 RSS 路径别名, 如 my-merged")
    max_items: int = Field(default=100, description="RSS 最大条目数")


class MergeGroupUpdate(BaseModel):
    """更新合并源请求。"""
    name: str | None = None
    description: str | None = None
    instance_ids: list[str] | None = None
    rss_slug: str | None = None
    max_items: int | None = None


class MergeGroupResponse(BaseModel):
    """合并源响应。"""
    id: str
    name: str
    description: str
    rss_token: str
    rss_slug: str | None = None
    rss_url: str = ""
    max_items: int
    instance_ids: list[str] = []
    instance_names: list[str] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
