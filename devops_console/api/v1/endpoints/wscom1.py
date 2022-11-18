# Copyright 2020 Croix Bleue du Québec
from anyio import create_task_group
from fastapi import APIRouter, WebSocket

from devops_console.clients.wscom import wscom_generic_handler
from .ws_dispatchers import kubernetes, oauth2, sccs

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

router = APIRouter()

handlers = {
    "k8s": kubernetes.wscom_dispatcher,
    "oauth2": oauth2.wscom_dispatcher,
    "sccs": sccs.wscom_dispatcher,
    }


@router.websocket("/wscom1")
async def wscom1_handler(websocket: WebSocket):
    """Websocket Com1"""

    async with create_task_group() as tg:
        result = await wscom_generic_handler(tg, websocket, handlers)

    return result
