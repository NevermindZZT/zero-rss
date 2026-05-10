"""SQLAlchemy ORM 模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from .database import Base


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class Script(Base):
    """脚本模板表 - 存储用户上传的 Python 脚本。"""

    __tablename__ = "scripts"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    version = Column(String(50), default="1.0.0")
    author = Column(String(255), default="")
    filename = Column(String(255), nullable=False, unique=True)
    code = Column(Text, nullable=False)
    params_schema = Column(Text, default="[]")  # JSON
    default_schedule = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    instances = relationship("Instance", back_populates="script", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Script(name={self.name!r}, filename={self.filename!r})>"


class Instance(Base):
    """脚本实例表 - 脚本模板 + 具体参数 = 独立运行的 RSS 源。"""

    __tablename__ = "instances"

    id = Column(String(36), primary_key=True, default=_uuid)
    script_id = Column(String(36), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    params = Column(Text, nullable=False, default="{}")  # JSON
    schedule_type = Column(String(20), default="interval")  # interval, cron, on_refresh, manual
    schedule_config = Column(Text, nullable=True)  # JSON
    rss_token = Column(String(64), nullable=False, unique=True, default=_uuid)
    enabled = Column(Integer, default=1)
    max_items = Column(Integer, default=100)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(20), nullable=True)  # success, error
    last_error = Column(Text, nullable=True)

    script = relationship("Script", back_populates="instances")
    rss_items = relationship("RSSItem", back_populates="instance", cascade="all, delete-orphan")
    run_history = relationship("RunHistory", back_populates="instance", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Instance(name={self.name!r}, script_id={self.script_id!r})>"


class RSSItem(Base):
    """RSS 条目表 - 每条独立的内容项。"""

    __tablename__ = "rss_items"

    id = Column(String(36), primary_key=True, default=_uuid)
    instance_id = Column(String(36), ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    guid = Column(String(512), nullable=False)
    title = Column(Text, default="")
    description = Column(Text, default="")
    link = Column(Text, default="")
    author = Column(String(255), default="")
    categories = Column(Text, default="[]")  # JSON 数组
    content = Column(Text, default="")
    image = Column(Text, default="")
    pub_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)

    instance = relationship("Instance", back_populates="rss_items")

    __table_args__ = (
        Index("idx_rss_items_instance", "instance_id"),
        Index("idx_rss_items_guid", "guid"),
    )

    def __repr__(self):
        return f"<RSSItem(title={self.title!r}, instance_id={self.instance_id!r})>"


class RunHistory(Base):
    """运行历史表 - 记录每次脚本执行的结果。"""

    __tablename__ = "run_history"

    id = Column(String(36), primary_key=True, default=_uuid)
    instance_id = Column(String(36), ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False)  # running, success, error
    items_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    instance = relationship("Instance", back_populates="run_history")

    __table_args__ = (
        Index("idx_run_history_instance", "instance_id"),
    )

    def __repr__(self):
        return f"<RunHistory(status={self.status!r}, instance_id={self.instance_id!r})>"


class MergeGroup(Base):
    """合并源表 - 将多个实例合并为一个 RSS 订阅源。"""

    __tablename__ = "merge_groups"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    rss_token = Column(String(64), nullable=False, unique=True, default=_uuid)
    max_items = Column(Integer, default=100)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    items = relationship("MergeGroupItem", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MergeGroup(name={self.name!r})>"


class MergeGroupItem(Base):
    """合并源成员表 - 记录合并源包含哪些实例。"""

    __tablename__ = "merge_group_items"

    id = Column(String(36), primary_key=True, default=_uuid)
    group_id = Column(String(36), ForeignKey("merge_groups.id", ondelete="CASCADE"), nullable=False)
    instance_id = Column(String(36), ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    sort_order = Column(Integer, default=0)

    group = relationship("MergeGroup", back_populates="items")
    instance = relationship("Instance")

    __table_args__ = (
        Index("idx_merge_group_items_group", "group_id"),
        Index("idx_merge_group_items_instance", "instance_id"),
    )

    def __repr__(self):
        return f"<MergeGroupItem(group={self.group_id}, instance={self.instance_id})>"
