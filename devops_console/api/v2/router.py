from devops_console.core import settings
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from .endpoints import auth, html, sccs, users, websocket, sse


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

# server-sent events
sse_router = APIRouter()
sse_router.include_router(
    sse.router,
    default_response_class=EventSourceResponse,
)


main_router = APIRouter()
main_router.include_router(api_router, tags=["api"])
main_router.include_router(html_router, tags=["frontend"])
main_router.include_router(sse_router, tags=["sse"])
