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

    async def init(self):
        self.core = await K8sCore.create(self.config)

    async def pods_watch(self, sccs_plugin, sccs_session, repository, environment):
        """Return a generator iterator of events for the pods of the given repository.
        see core.py in python-devops-kubernetes for the event shape.
        """
        clusters: list[str] = self.config["clusters"].keys()

        suffixmap = {
            "accept-2": "accept2",
            "acceptation": "accept",
            "development": "dev",
            "development-2": "dev2",
            "master": None,
            "pre-production": "preprod",
            "production": "prod",
            "qa": "qa",
            "quality-assurance-2": "qa2",
            "training": "formation",
        }

        env: str = suffixmap[environment] if environment in suffixmap else environment

        namespace = repository + "-" + env if env else repository

        async def gen():
            nonlocal namespace
            nonlocal clusters
            for cluster in clusters:
                yield {
                    "type": "INFO",
                    "key": "bridge",
                    "value": {
                        "cluster": cluster,
                        "namespace": namespace,
                        "repository": {
                            "write_access": False,
                        },
                    },
                }
                async with self.core.context(cluster=cluster) as ctx:
                    async for event in ctx.pods(namespace):
                        yield event

        return gen()

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
