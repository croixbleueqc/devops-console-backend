# Copyright 2020 Croix Bleue du Québec

from devops_console.clients.client import CoreClient
from devops_console.clients.wscom import DispatcherUnsupportedRequest

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


intervals = {
    "repositories": 3600,
    "cd": 30,
    "cd_versions_available": 30,
    "cd_environments_available": 30,
}


async def wscom_dispatcher(request, action: str, path: str, body: dict):
    client = CoreClient().sccs

    plugin_id = body.get("plugin")
    credentials = body.get("session")
    repo_name = body.get("repository")
    environment = body.get("environment")
    args = body.get("args") or {}

    if action == "read":
        if path == "/repositories":
            return await client.get_repositories(plugin_id, credentials)
        elif path == "/repository/cd/config":
            return await client.get_continuous_deployment_config(plugin_id, credentials)
        elif path == "/repository/cd/environments_available":
            return await client.get_continuous_deployment_environments_available(
                plugin_id, credentials, repo_name, **args
            )
        elif path == "/repository/add/contract":
            return await client.get_add_repository_contract(plugin_id, credentials)
        elif path == "/repositories/compliance/report":
            return await client.compliance_report(
                plugin_id, credentials, **args
            )
    elif action == "watch":
        if path == "/repositories":
            return client.watch_repositories(
                plugin_id, credentials, poll_interval=intervals["repositories"], **args
            )
        elif path == "/repository/cd/config":
            environments = body.get("environments")

            if environments is None:
                environments = []

            return client.watch_continuous_deployment_config(
                plugin_id, credentials, repo_name, environments, poll_interval=intervals["cd"], **args, )
        elif path == "/repository/cd/versions_available":
            return client.watch_continuous_deployment_versions_available(
                plugin_id, credentials, repo_name, poll_interval=intervals["cd_versions_available"], **args
            )
        elif path == "/repository/cd/environments_available":
            return client.watch_continuous_deployment_environments_available(
                plugin_id, credentials, repo_name, poll_interval=intervals["cd_environments_available"], **args
            )
    elif action == "write":
        if path == "/repository/cd/trigger":
            return (await client.trigger_continuous_deployment(
                plugin_id, credentials, repo_name, environment, body["version"], **args, )).dict()
        elif path == "/repository/add":
            return await client.add_repository(
                plugin_id, credentials, repo_name, body["template"], body["template_params"], **args
            )
    elif action == "":
        if path == "/passthrough":
            return await client.passthrough(
                plugin_id, credentials, body["request"], **args
            )

    raise DispatcherUnsupportedRequest(action, path)
