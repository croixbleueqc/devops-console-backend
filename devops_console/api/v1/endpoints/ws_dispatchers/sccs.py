# Copyright 2020 Croix Bleue du Québec

from enum import IntEnum

from anyio import Event
from anyio.streams.memory import MemoryObjectSendStream

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


class Intervals(IntEnum):
    repositories = 3600
    cd = 3600
    cd_versions_available = 3600
    cd_environs_available = 3600


async def wscom_dispatcher(
        action: str,
        path: str,
        body: dict,
        send_stream: MemoryObjectSendStream | None = None,
        cancel_event: Event | None = None,
        ):
    client = CoreClient().sccs

    plugin_id = body.get("plugin")
    credentials = body.get("session")
    repo_name = body.get("repository")
    environment = body.get("environment")
    environments = body.get("environments", [])
    kwargs = body.get("args") or {}

    if action == "read":
        if path == "/repositories":
            return await client.get_repositories(plugin_id, credentials)
        elif path == "/repository/cd/config":
            return await client.get_continuous_deployment_config(
                plugin_id,
                credentials,
                repo_name,
                environments
                )
        elif path == "/repository/cd/environments_available":
            return await client.get_continuous_deployment_environments_available(
                plugin_id, credentials, repo_name, **kwargs
                )
        elif path == "/repository/add/contract":
            return await client.get_add_repository_contract(plugin_id, credentials)
        elif path == "/repositories/compliance/report":
            return await client.compliance_report(plugin_id, credentials, **kwargs)

    elif action == "watch":
        if send_stream is None or cancel_event is None:
            raise DispatcherUnsupportedRequest(
                "Watch requests must be made with a send stream and a cancel event"
                )
        if path == "/repositories":
            await client.watch_repositories(
                plugin_id,
                credentials,
                Intervals.repositories,
                send_stream,
                cancel_event,
                )
        elif path == "/repository/cd/config":
            await client.watch_continuous_deployment_config(
                plugin_id,
                credentials,
                Intervals.cd,
                send_stream,
                cancel_event,
                repo_name,
                environments,
                )
        elif path == "/repository/cd/versions_available":
            await client.watch_continuous_deployment_versions_available(
                plugin_id,
                credentials,
                Intervals.cd_versions_available,
                send_stream,
                cancel_event,
                repo_name,
                )
        elif path == "/repository/cd/environments_available":
            await client.watch_continuous_deployment_environments_available(
                plugin_id,
                credentials,
                Intervals.cd_environs_available,
                send_stream,
                cancel_event,
                repo_name,
                )
        return
    elif action == "write":
        if path == "/repository/cd/trigger":
            return (await client.trigger_continuous_deployment(
                plugin_id,
                credentials,
                repo_name,
                environment,
                body["version"],
                )).dict()
        elif path == "/repository/add":
            return await client.add_repository(
                plugin_id,
                credentials,
                repo_name,
                body["template"],
                body["template_params"],
                **kwargs
                )
    elif action == "":
        if path == "/passthrough":
            return await client.passthrough(plugin_id, credentials, body["request"], **kwargs)

    raise DispatcherUnsupportedRequest(action, path)
