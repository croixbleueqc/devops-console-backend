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

from devops_kubernetes.core import Core as K8sCore
from devops_sccs.errors import AccessForbidden


class Kubernetes(object):
    def __init__(self, config, sccs):
        self.config = config
        self.sccs = sccs
        self.core: K8sCore

    async def init(self, app):
        self.core = await K8sCore.create(self.config)

    async def pods_watch(self, sccs_plugin, sccs_session, repository, environment):
        bridge = await self.sccs.bridge_repository_to_namespace(
            sccs_plugin, sccs_session, repository, environment
        )

        async def pods_watch_with_bridge_info():
            yield {"type": "INFO", "key": "bridge", "value": bridge}

            async with self.core.context(bridge["cluster"]) as ctx:
                async for event in ctx.pods(bridge["namespace"]):
                    yield event

        return pods_watch_with_bridge_info()

    async def delete_pod(
        self, sccs_plugin, sccs_session, repository, environment, pod_name
    ):
        bridge = await self.sccs.bridge_repository_to_namespace(
            sccs_plugin, sccs_session, repository, environment
        )

        if not bridge["repository"]["write_access"]:
            raise AccessForbidden(
                f"You don't have write access on {repository} to delete a pod"
            )

        async with self.core.context(bridge["cluster"]) as ctx:
            await ctx.delete_pod(pod_name, bridge["namespace"])
