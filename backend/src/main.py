"""zero-rss 后端应用入口。

FastAPI 应用初始化、路由注册、生命周期事件。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import init_db, close_db
from .api.scripts import router as scripts_router
from .api.instances import router as instances_router
from .api.rss import router as rss_router
from .api.system import router as system_router
from .core.scheduler import start_scheduler, stop_scheduler


# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("zero-rss")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    logger.info("Starting zero-rss backend...")
    await init_db()
    logger.info("Database initialized")
    await start_scheduler()
    logger.info("Scheduler started")
    yield
    await stop_scheduler()
    await close_db()
    logger.info("zero-rss backend stopped")


app = FastAPI(
    title="zero-rss",
    description="私有化 RSS 订阅系统 - 用户自定义脚本生成 RSS 订阅源",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置 (前端开发时使用)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(scripts_router)
app.include_router(instances_router)
app.include_router(rss_router)
app.include_router(system_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理。"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
async def root():
    """根路径 - API 信息。"""
    return {
        "name": "zero-rss",
        "version": "1.0.0",
        "docs": "/docs",
    }
