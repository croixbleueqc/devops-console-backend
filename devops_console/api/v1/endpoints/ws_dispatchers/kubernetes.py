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


from devops_console.clients.client import CoreClient
from devops_console.clients.wscom import DispatcherUnsupportedRequest


async def wscom_dispatcher(request, action, path, body):
    core = CoreClient()
    if action == "watch":
        if path == "/pods":
            return await core.kubernetes.pods_watch(
                body["sccs_plugin"],
                body["sccs_session"],
                body["repository"],
                body["environment"],
                )
    elif action == "delete":
        if path == "/pod":
            return await core.kubernetes.delete_pod(
                body["sccs_plugin"],
                body["sccs_session"],
                body["repository"],
                body["environment"],
                body["name"],
                )

    raise DispatcherUnsupportedRequest(action, path)
