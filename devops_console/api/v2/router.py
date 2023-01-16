from fastapi import APIRouter
# from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from devops_console.core import settings
from .endpoints import sccs, sse, websocket, k8s, admin

api_router = APIRouter(prefix=settings.API_V2_STR)

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
    k8s.router,
    prefix="/k8s",
    tags=["k8s"],
    )

api_router.include_router(
    admin.router,
    tags=["admin"],
    )

# # frontend
# html_router = APIRouter()
# html_router.include_router(
#     html.router,
#     default_response_class=HTMLResponse,
# )

# server-sent events
api_router.include_router(
    sse.router,
    default_response_class=EventSourceResponse,
    tags=["sse"]
    )

main_router = APIRouter()
main_router.include_router(api_router)
# main_router.include_router(html_router, tags=["frontend"])
