# Copyright 2020 Croix Bleue du Québec

# This file is part of devops-console-backend.

# devops-console-backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# devops-console-backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with devops-console-backend.  If not, see <https://www.gnu.org/licenses/>.

import json
import logging
from typing import Any

from anyio import (
    create_memory_object_stream,
    create_task_group,
    Event,
    )
from fastapi import WebSocket
from requests import HTTPError
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosed

from devops_console.schemas.legacy.ws import WsResponse


class ConnectionManager:
    def __init__(self):
        self.ws_set: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.ws_set.add(websocket)

    async def broadcast(self, data: str | dict, legacy: bool = False) -> None:
        if legacy:
            data = WsResponse(
                "whitecard", data_response=data if isinstance(data, dict) else {"message": data}
                ).json()
        for websocket in self.ws_set:
            await websocket.send_json(data)

    async def send_json(self, websocket: WebSocket, data: Any):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logging.error(f"Error sending data to websocket: {e}")
            raise
        except ConnectionClosed:
            await self.disconnect(websocket)

    async def disconnect(self, websocket: WebSocket):
        try:
            # del self.ws_watchers_map[hash(websocket)]
            self.ws_set.remove(websocket)
        except (KeyError, ValueError):
            pass


manager = ConnectionManager()
cancel_events = {}


async def wscom_generic_handler(websocket: WebSocket, handlers: dict):
    """Websocket Generic handler

    This generic handler will respond to a specific message type only.
    By security, if the message is malformed, the websocket will be closed.

    Message expected:
    {
        "uniqueId": "<str>",
        "request": "<deeplink>:<action>:<path>",
        "dataRequest": <json values>
    }

    Response on success:
    {
        "uniqueId": "<str>",
        "dataResponse": <json values>
    }

    Response on error:
    {
        "uniqueId": "<str>",
        "error": "<str>"
    }

    Reserved Messages request are:
    - "ws:ctl:close" : Ask the server to close the websocket
    - "ws:watch:close" : Ask the server to close a watcher for the current websocket

    """

    global manager
    global cancel_events

    await manager.connect(websocket)

    async with create_task_group() as tg:
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                    unique_id = data["uniqueId"]
                    request_headers = data.pop("request")
                    body = data.pop("dataRequest")

                    logging.debug(f"RECEIVED WS REQUEST: {request_headers}")

                    deeplink, action, path = request_headers.split(":")
                except (AttributeError, ValueError, json.decoder.JSONDecodeError):
                    # Malformed request.
                    logging.error("malformed request. ws will be closed")

                    # Closing the websocket
                    break

                if deeplink == "ws":
                    if request_headers == "ws:ctl:close":
                        # Closing the websocket
                        break

                    elif request_headers == "ws:watch:close":
                        # Closing a watcher for this websocket
                        tg.start_soon(wscom_watcher_close, websocket, unique_id, data)

                    else:
                        data["error"] = f"The server doesn't support {request_headers}"
                        logging.warning(data["error"])
                        await websocket.send_json(data)

                    # Internal dispatch done
                    continue

                handler = handlers[deeplink]

                if handler is None:
                    data["error"] = f"There is no handler to support {deeplink}"
                    logging.warning(data["error"])
                    await websocket.send_json(data)
                elif action == "watch":
                    cancel_event = cancel_events.get(unique_id, Event())
                    cancel_events[unique_id] = cancel_event
                    tg.start_soon(
                        wscom_watcher_run,
                        websocket,
                        handler,
                        data,
                        action,
                        path,
                        body,
                        cancel_event,
                        )
                else:
                    tg.start_soon(
                        wscom_restful_run,
                        websocket,
                        handler,
                        data,
                        action,
                        path,
                        body
                        )
        except (WebSocketDisconnect, HTTPError) as e:
            cancel_all_watchers()
            if isinstance(e, HTTPError):
                logging.error(e)
        finally:
            tg.cancel_scope.cancel()
            await manager.disconnect(websocket)

    return websocket


def format_result_for_send(a):
    return a.dict() if hasattr(a, "dict") else a


def cancel_all_watchers():
    global cancel_events
    for cancel_event in cancel_events.values():
        cancel_event.set()
    cancel_events.clear()


async def wscom_restful_run(websocket, handler, data, action, path, body):
    """RESTful like request"""
    try:
        result = await handler(action, path, body)
        data["dataResponse"] = format_result_for_send(result)
        await manager.send_json(websocket, data)
    except Exception as e:
        data["error"] = str(e)
        await manager.send_json(websocket, data)


async def wscom_watcher_run(websocket, handler, data, action, path, body, cancel_event):
    """Watch request"""

    async def receive_handler_events(receive_stream):
        try:
            async with receive_stream:
                async for event in receive_stream:
                    data["dataResponse"] = event.dict() if hasattr(event, "dict") else event
                    await manager.send_json(websocket, data)
        except Exception as e:
            data["error"] = str(e)
            await manager.send_json(websocket, data)
            raise

    send_stream, receive_stream = create_memory_object_stream()

    async with create_task_group() as tg:
        tg.start_soon(receive_handler_events, receive_stream)
        tg.start_soon(handler, action, path, body, send_stream, cancel_event)


async def wscom_watcher_close(websocket, unique_id, data=None):
    cancel_event = cancel_events.get(unique_id)
    if cancel_event is not None:
        cancel_event.set()
        del cancel_events[unique_id]
    else:
        return

    if websocket is not None and data is not None:
        data["dataResponse"] = {"status": "ws:watch:closed"}
        try:
            await manager.send_json(websocket, data)
        except ConnectionResetError:
            # Most of the time we can send back an answer but if the application is closing it is
            # possible that ws was disconnected before the send_json.
            pass


class DispatcherUnsupportedRequest(Exception):
    def __init__(self, action, path):
        Exception.__init__(
            self,
            f"Dispatcher does not support {action}:{path} with provided dataRequest",
            )


class DeepLinkAlreadySet(Exception):
    def __init__(self, deeplink, dispatchers_app_key):
        Exception.__init__(
            self,
            f"The deeplink {deeplink} is already registred for {dispatchers_app_key}",
            )


def wscom_setup(app, dispatchers_app_key, deeplink, dispatch):
    """Setup a dispatcher function for a deeplink

    Final target is a dict of dispatcher functions for all deeplink that will be received on the websocket.

    app[dispatchers_app_key] = {
            "<deeplink 1>": dispatch_func1,
            "<deeplink 2>": dispatch_func2,
            ...
        }
    """

    if app.get(dispatchers_app_key) is None:
        app[dispatchers_app_key] = {}

    if app[dispatchers_app_key].get(deeplink) is not None:
        raise DeepLinkAlreadySet(deeplink, dispatchers_app_key)

    app[dispatchers_app_key][deeplink] = dispatch
