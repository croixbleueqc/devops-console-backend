from fastapi import APIRouter

from .endpoints import health, wscom1

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(wscom1.router, tags=["websocket"])
