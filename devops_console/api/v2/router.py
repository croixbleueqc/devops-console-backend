from devops_console.api.deps import validate_token
from devops_console.core import settings
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from .endpoints import auth, html, sccs, users, websocket

api_router = APIRouter(prefix=settings.API_V2_STR)

api_router.include_router(auth.router, tags=["token"])
api_router.include_router(
    sccs.router,
    prefix="/sccs",
    tags=["sccs"],
)
api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["websocket"],
)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)

# frontend
html_router = APIRouter()
html_router.include_router(
    html.router,
    default_response_class=HTMLResponse,
)


router = APIRouter()
router.include_router(api_router, tags=["api"])
router.include_router(html_router, tags=["frontend"])
