"""Token 认证中间件。"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

security = HTTPBearer(auto_error=False)

# RSS 订阅端点无需认证
PUBLIC_PATHS = {"/health", "/rss"}


async def verify_token(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> bool:
    """验证 Bearer Token。

    对所有 /api/* 路径进行认证检查。
    RSS 订阅端点 /rss/* 无需认证。
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.credentials != settings.auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
