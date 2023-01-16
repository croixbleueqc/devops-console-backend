import asyncio
import logging
from typing import Any

from anyio import create_memory_object_stream
from anyio.streams.memory import MemoryObjectSendStream
from fastapi import Request
from pydantic import BaseModel
from sse_starlette import ServerSentEvent

from devops_console.clients import CoreClient
from devops_console.schemas import WebhookEventKey

client = CoreClient().sccs


class SseData(BaseModel):
    repo_slug: str
    environment: str | None
    event_key: WebhookEventKey | None
    data: Any


class SseGenerator:
    streams: set[MemoryObjectSendStream]

    def __init__(self):
        self.streams = set()

    async def broadcast(self, data: SseData):
        """ Receive an event from the listening
        webhook server and transmit it to all subscribers. """
        for stream in self.streams:
            async with stream:
                # TODO: use event type strings (probably webhook event keys)
                await stream.send(ServerSentEvent(data=data))

    async def subscribe(self, repo_slug: str, environment: str, request: Request):
        """Create an object stream and return an async generator function that yields a
        dict each time an event is received on the stream."""
        send_stream, receive_stream = create_memory_object_stream()
        self.streams.add(send_stream)

        async def generator():
            try:
                async with receive_stream:
                    async for event in receive_stream:
                        if event.repo_slug == repo_slug:
                            # FIXME, maybe add event.environment == environment:
                            yield event.dict()
            except asyncio.CancelledError as e:
                logging.info(f"Disconnected from client {request.client}")
                raise e
            self.streams.remove(send_stream)

        return generator


sse_generator = SseGenerator()
