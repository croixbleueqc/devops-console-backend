from devops_console.core import settings
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .endpoints import auth, bitbucket, html, users, websocket

router = APIRouter(prefix=settings.API_V2_STR)

router.include_router(auth.router, tags=["token"])
router.include_router(bitbucket.router, prefix="/bb", tags=["bitbucket"])
router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
router.include_router(users.router, prefix="/users", tags=["users"])

# frontend
router.include_router(
    html.router,
    tags=["frontend"],
    default_response_class=HTMLResponse,
)
