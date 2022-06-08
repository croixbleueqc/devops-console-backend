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

from ...core import Core
from ...wscom import DispatcherUnsupportedRequest

# WebSocket (wscom) section


async def wscom_dispatcher(request, action, path, body):
    core: Core = request.config_dict["core"]

    if action == "read":
        if path == "/repositories":
            return await core.sccs.get_repositories(
                body["plugin"], body["session"], body.get("args")
            )
        elif path == "/repository/cd/config":
            return (
                await core.sccs.get_continuous_deployment_config(
                    body["plugin"],
                    body["session"],
                    body["repository"],
                    body.get("environments"),
                    body.get("args"),
                )
            ).dumps()
        elif path == "/repository/cd/environments_available":
            return await core.sccs.get_continuous_deployment_environments_available(
                body["plugin"], body["session"], body["repository"], body.get("args")
            )
        elif path == "/repository/add/contract":
            return await core.sccs.get_add_repository_contract(
                body["plugin"], body["session"]
            )
        elif path == "/repositories/compliance/report":
            return await core.sccs.compliance_report(
                body["plugin"], body["session"], body.get("args")
            )
    elif action == "watch":
        if path == "/repositories":
            return core.sccs.watch_repositories(
                plugin_id=body["plugin"], session=body["session"], args=body.get("args")
            )
        elif path == "/repository/cd/config":
            return core.sccs.watch_continuous_deployment_config(
                body["plugin"],
                body["session"],
                body["repository"],
                body.get("environments"),
                body.get("args"),
            )
        elif path == "/repository/cd/versions_available":
            return core.sccs.watch_continuous_deployment_versions_available(
                body["plugin"], body["session"], body["repository"], body.get("args")
            )
        elif path == "/repository/cd/environments_available":
            return core.sccs.watch_continuous_deployment_environments_available(
                body["plugin"], body["session"], body["repository"], body.get("args")
            )
    elif action == "write":
        if path == "/repository/cd/trigger":
            return (
                await core.sccs.trigger_continuous_deployment(
                    body["plugin"],
                    body["session"],
                    body["repository"],
                    body["environment"],
                    body["version"],
                    body.get("args"),
                )
            ).dumps()
        elif path == "/repository/add":
            return await core.sccs.add_repository(
                body["plugin"],
                body["session"],
                body["repository"],
                body.get("template"),
                body.get("template_params"),
                body.get("args"),
            )
    elif action == "":
        if path == "/passthrough":
            return await core.sccs.passthrough(
                body["plugin"], body["session"], body["request"], body.get("args")
            )

    raise DispatcherUnsupportedRequest(action, path)
