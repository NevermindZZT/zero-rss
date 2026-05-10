"""应用配置管理 - 从环境变量加载配置。"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置。

    从环境变量加载，支持 .env 文件。
    """

    # 认证
    auth_token: str = "your-secret-token-here"

    # 数据库
    database_url: str = "sqlite+aiosqlite:///data/rss.db"

    # 脚本目录
    scripts_dir: str = "/app/scripts"

    # 日志
    log_level: str = "INFO"

    # 服务器
    host: str = "0.0.0.0"
    port: int = 11080

    # 外部访问地址 (用于生成 RSS 订阅链接)
    # 如果设置了此项, RSS 链接会使用这个地址而不是 host:port
    # 例如: https://rss.example.com
    external_url: str = ""

    # 脚本执行
    script_timeout: int = 60

    @property
    def db_path(self) -> str:
        """获取数据库文件路径 (去掉 sqlite+aiosqlite:/// 前缀)。"""
        return self.database_url.replace("sqlite+aiosqlite:///", "")

    @property
    def scripts_dir_path(self) -> Path:
        """获取脚本目录的 Path 对象。"""
        return Path(self.scripts_dir)

    @property
    def base_url(self) -> str:
        """获取外部访问基础 URL。

        优先使用 external_url 配置, 否则使用 host:port 拼接。
        """
        if self.external_url:
            return self.external_url.rstrip("/")
        return f"http://127.0.0.1:{self.port}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保数据目录和数据文件所在目录存在
_db_path = settings.db_path
_db_dir = os.path.dirname(_db_path)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)
os.makedirs(settings.scripts_dir, exist_ok=True)
