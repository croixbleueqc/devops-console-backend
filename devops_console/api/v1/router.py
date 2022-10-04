from fastapi import APIRouter

from devops_console.core import settings

from .endpoints import health, wscom1

router = APIRouter(prefix=settings.API_V1_STR)

router.include_router(health.router, tags=["health"])
router.include_router(wscom1.router, tags=["websocket"])
