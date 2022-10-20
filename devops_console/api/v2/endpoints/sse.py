from fastapi import APIRouter, Depends

from devops_console.clients.client import CoreClient

client = CoreClient().sccs

router = APIRouter(prefix="/sse")


@router.get("/cd")
async def sse_endpoint(repo_name: str, env_name: str = "", session=Depends()):
    plugin_id, credentials = session

    # TODO; maybe...
