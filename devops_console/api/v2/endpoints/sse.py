from fastapi import APIRouter, Request
from sse_starlette import EventSourceResponse

from devops_console.clients.client import CoreClient
from devops_console.sse_event_generator import sse_generator

client = CoreClient().sccs

router = APIRouter(prefix="/sse")


@router.get("/cd/{repo_slug}/{env_name}")
async def sse_endpoint(repo_slug: str, env_name: str, request: Request):
    generator = sse_generator.subscribe(repo_slug, env_name, request)

    # async def test_gen():
    #     try:
    #         while True:
    #             yield {
    #                 "event": "test",
    #                 "data": "hello"
    #                 }
    #             await asyncio.sleep(5)
    #     except asyncio.CancelledError as e:
    #         logging.info(f"Disconnected from client {req.client}")
    #         raise e

    return EventSourceResponse(generator)
