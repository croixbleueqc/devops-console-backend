from devops_console.clients.client import CoreClient

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from .sccs import get_bitbucket_session

client = CoreClient().sccs

router = APIRouter(prefix="/sse")


@router.get("/cd")
async def sse_endpoint(
    repo_name: str, env_name: str = "", bitbucket_session=Depends(get_bitbucket_session)
):
    plugin_id, session = bitbucket_session

    async def gen():
        async for event in client.watch_continuous_deployment_config(
            plugin_id,
            session,
            repo_name,
            environments=[env_name],
            args=None,
        ):
            yield ServerSentEvent(data=event.value.version, event="cd_version")

    return EventSourceResponse(gen())
