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

from anyio import create_memory_object_stream, create_task_group
from anyio.abc import TaskGroup
from fastapi import WebSocket, WebSocketDisconnect
from requests import HTTPError
from websockets.exceptions import ConnectionClosed

from devops_console.schemas.legacy.ws import WsResponse

WATCHERS = "watchers"


# Watchers = weakref.WeakValueDictionary[int, asyncio.Task]


class ConnectionManager:
    def __init__(self):
        # self.ws_watchers_map: dict[int, Watchers] = {}
        self.ws_set: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        # self.ws_watchers_map[hash(websocket)] = weakref.WeakValueDictionary()
        self.ws_set.add(websocket)

    # def add_watcher(self, websocket: WebSocket, watcher_id: int, task: asyncio.Task):
    #     h = hash(websocket)
    #     # d = self.ws_watchers_map.get(h, weakref.WeakValueDictionary())
    #     d[watcher_id] = task

    # def get_watcher(self, websocket: WebSocket, watcher_id: int) -> asyncio.Task | None:
    #     h = hash(websocket)
    #     try:
    #         return self.ws_watchers_map[h][watcher_id]
    #     except KeyError:
    #         return None

    # def get_watchers(self, websocket: WebSocket) -> Watchers | None:
    #     h = hash(websocket)
    #     return self.ws_watchers_map.get(h, None)

    # def remove_watcher(self, websocket: WebSocket, watcher_id: int) -> None:
    #     h = hash(websocket)
    #     try:
    #         del self.ws_watchers_map[h][watcher_id]
    #     except (KeyError, ValueError):
    #         pass
    #
    # async def close_watchers(self, websocket: WebSocket) -> None:
    #     watchers = self.get_watchers(websocket)
    #     if watchers is not None:
    #         for watcher_id in watchers.keys():
    #             await wscom_watcher_close(websocket, watcher_id)
    #             try:
    #                 del watchers[watcher_id]
    #             except (KeyError, ValueError):
    #                 pass

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


async def wscom_generic_handler(tg: TaskGroup, websocket: WebSocket, handlers: dict):
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
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            try:
                uniqueId = data["uniqueId"]
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
                    await wscom_watcher_close(websocket, uniqueId)

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
                tg.start_soon(wscom_watcher_run, websocket, handler, data, action, path, body)
            else:
                tg.start_soon(wscom_restful_run, websocket, handler, data, action, path, body)

    except (WebSocketDisconnect, HTTPError) as e:
        await manager.disconnect(websocket)
        if isinstance(e, HTTPError):
            logging.error(e)
    finally:
        # Closes all watchers for this request
        # await manager.close_watchers(websocket)

        # Removes websocket
        await manager.disconnect(websocket)

    return websocket


def format_result_for_send(a):
    return a.dict() if hasattr(a, "dict") else a


async def wscom_restful_run(websocket, handler, data, action, path, body):
    """RESTful like request"""
    try:
        result = await handler(action, path, body)
        data["dataResponse"] = format_result_for_send(result)
        await manager.send_json(websocket, data)
    except Exception as e:
        data["error"] = str(e)
        await manager.send_json(websocket, data)


async def wscom_watcher_run(websocket, handler, data, action, path, body):
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
        async with send_stream:
            await handler(action, path, body, send_stream)


async def wscom_watcher_close(websocket, uniqueId, data=None):
    """Closes a watcher

    ws and data are needed to send back a closed answer
    """
    # try:
    #     task = manager.get_watcher(websocket, uniqueId)
    # except KeyError:
    #     return
    #
    # if task is None:
    #     return
    #
    # task.cancel()
    #
    # try:
    #     await task
    # except Exception as e:
    #     if data is not None:
    #         data["error"] = repr(e)
    #     logging.error(
    #         f"{uniqueId}: something wrong occured during watcher closing. error: {repr(e)}"
    #         )

    if websocket is not None and data is not None:
        data["dataResponse"] = {"status": "ws:watch:closed"}
        try:
            await manager.send_json(websocket, data)
        except ConnectionResetError:
            # Most of the time we can send back an answer but if the application is closing it is possible that ws was
            # disconnected before the send_json.
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
