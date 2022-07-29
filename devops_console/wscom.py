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

from aiohttp import web, WSMsgType
import asyncio
import logging
import json
import weakref
from typing_engine.typing import Typing2

WATCHERS = "ws_watchers"


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Typing2):
            return obj.dumps()
        return json.JSONEncoder.default(self, obj)


def custom_dumps(obj):
    return json.dumps(obj, cls=CustomEncoder)


async def wscom_generic_handler(request, dispatchers_app_key):
    """Websocket Generic handler

    This generic handler will respond to a specific message type only.
    By security, if the message is malformed, the websocket will be closed.

    This handler is using dispatcher functions set with wscom_setup()

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
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    logging.info("connected")
    print("wscom_generic_handler: connected")

    request.app["websockets"].add(ws)
    request[WATCHERS] = weakref.WeakValueDictionary()
    dispatchers = request.app.get(dispatchers_app_key, {})
    try:
        async for msg in ws:
            print(f"received websocket message:\n {msg}")
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    uniqueId = data["uniqueId"]
                    request_headers = data.pop("request")
                    body = data.pop("dataRequest")

                    deeplink, action, path = request_headers.split(":")
                except (AttributeError, ValueError, json.decoder.JSONDecodeError):
                    # Malformed request.
                    logging.error(f"malformed request. ws will be closed")

                    # Closing the websocket
                    break

                if deeplink == "ws":
                    if request_headers == "ws:ctl:close":
                        # Closing the websocket
                        break

                    elif request_headers == "ws:watch:close":
                        # Closing a watcher for this websocket
                        asyncio.create_task(
                            wscom_watcher_close(request, uniqueId, ws=ws, data=data)
                        )

                    else:
                        data["error"] = f"The server doesn't support {request_headers}"
                        logging.warning(data["error"])
                        await ws.send_json(data, dumps=custom_dumps)

                    # Internal dispatch done
                    continue

                dispatch = dispatchers.get(deeplink)

                if dispatch is None:
                    data["error"] = f"There is no dispatcher to support {deeplink}"
                    logging.warning(data["error"])
                    await ws.send_json(data, dumps=custom_dumps)
                elif action == "watch":
                    logging.info(f"watching {request_headers}")

                    task = asyncio.create_task(
                        wscom_watcher_run(
                            request, ws, dispatch, data, action, path, body
                        ),
                        name=uniqueId,
                    )

                    request[WATCHERS][uniqueId] = task

                else:
                    logging.info(f"dispatching {request_headers}")

                    asyncio.create_task(
                        wscom_restful_run(
                            request, ws, dispatch, data, action, path, body
                        )
                    )

            elif msg.type == WSMsgType.ERROR:
                logging.error(
                    "ws connection closed with exception {}".format(ws.exception())
                )
    finally:
        logging.info("disconnected")

        # Removes websocket
        request.app["websockets"].discard(ws)

        # Closes all watchers for this request
        for uniqueId in tuple(request[WATCHERS].keys()):
            await wscom_watcher_close(request, uniqueId)

    return ws


async def wscom_restful_run(request, ws, dispatch, data, action, path, body):
    """RESTful like request"""
    try:
        data["dataResponse"] = await dispatch(request, action, path, body)
    except Exception as e:
        data["error"] = repr(e)
    await ws.send_json(data, dumps=custom_dumps)


async def wscom_watcher_run(request, ws, dispatch, data, action, path, body):
    """Watch request"""
    try:
        async for event in (await dispatch(request, action, path, body)):
            data["dataResponse"] = event
            logging.debug("received an event")
            await ws.send_json(data, dumps=custom_dumps)
    except Exception as e:
        data["error"] = repr(e)
        data["dataResponse"] = None
        logging.exception(repr(e))
        await ws.send_json(data, dumps=custom_dumps)


async def wscom_watcher_close(request, uniqueId, ws=None, data=None):
    """Closes a watcher

    ws and data are needed to send back a closed answer
    """
    try:
        task = request[WATCHERS].pop(uniqueId)
    except KeyError:
        logging.info(f"{uniqueId}: watcher already closed")
        return

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    except Exception as e:
        if data is not None:
            data["error"] = repr(e)
        logging.error(
            f"{uniqueId}: something wrong occured during watcher closing. error: {repr(e)}"
        )

    if ws is not None and data is not None:
        data["dataResponse"] = {"status": "ws:watch:closed"}
        try:
            await ws.send_json(data=data)
        except ConnectionResetError:
            # Most of the time we can send back an answer but if the application is closing it is possible that ws was disconnected before the send_json.
            pass

    logging.info(f"{uniqueId}: watcher closed")


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
