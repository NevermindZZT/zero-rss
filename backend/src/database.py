"""数据库引擎与会话管理。"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""
    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncSession:
    """获取数据库会话的依赖注入。

    在 FastAPI 中作为 Depends 使用:
        async def handler(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表结构。"""
    async with engine.begin() as conn:
        from . import models  # noqa: F401 - 确保模型注册
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接。"""
    await engine.dispose()
