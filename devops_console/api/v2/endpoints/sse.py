from devops_console.clients.client import CoreClient

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from .sccs import yield_credentials

client = CoreClient().sccs

router = APIRouter(prefix="/sse")


@router.get("/cd")
async def sse_endpoint(repo_name: str, env_name: str = "", session=Depends(yield_credentials)):
    plugin_id, credentials = session

    # TODO; maybe...
