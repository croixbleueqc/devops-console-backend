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

from aiohttp import web
from ...wscom import wscom_generic_handler

routes = web.RouteTableDef()

DISPATCHERS_APP_KEY = "wscom1_dispatchers"


@routes.get("/wscom1")
async def wscom1_handler(request):
    """Websocket Com1"""

    ws = await wscom_generic_handler(request, DISPATCHERS_APP_KEY)

    return ws
