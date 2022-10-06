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

import logging
import os

from devops_kubernetes.client import K8sClient
from devops_sccs.errors import AccessForbidden
from ..schemas.userconfig import KubernetesConfig
from ..clients.sccs import Sccs


class Kubernetes(object):
    def __init__(self, config: KubernetesConfig, sccs: Sccs):
        self.config = config
        self.sccs = sccs
        self.client: K8sClient

        # list cluster names on disk
        self.clusters = os.listdir(self.config.config_dir)

    async def init(self):
        self.client = await K8sClient.create(self.config.dict())

    def repo_to_namespace(self, repository, environment):
        env: str = (
            self.config.suffix_map[environment]
            if environment in self.config.suffix_map.keys()
            else environment
        )
        return f"{repository}-{env}"

    async def get_pod_clusters(self, namespace) -> list[str]:
        pod_clusters: list[str] = []
        for cluster in self.clusters:
            try:
                async with self.client.context(cluster) as ctx:
                    pods = await ctx.list_pods(namespace)
                    if len(pods) > 0:
                        pod_clusters.append(cluster)
            except Exception:
                pass

        logging.info(f"{namespace} is in the following clusters: {pod_clusters}")
        return pod_clusters

    async def pods_watch(self, sccs_plugin, sccs_session, repo_name, environment):
        """Return a generator iterator of events for the pods of the given repository.
        see client.py in python-devops-kubernetes for the event shape.
        """

        namespace = self.repo_to_namespace(repo_name, environment)

        pod_clusters = await self.get_pod_clusters(namespace)

        write_access = await self.write_access(sccs_plugin, sccs_session, repo_name)

        async def gen():
            nonlocal namespace
            nonlocal pod_clusters

            if len(pod_clusters) == 0:
                logging.warning(f"No cluster found for namespace {namespace}.")
                yield None
                return

            for cluster in pod_clusters:
                yield {
                    "type": "INFO",
                    "key": "bridge",
                    "value": {
                        "cluster": cluster,
                        "namespace": namespace,
                        "repository": {
                            "write_access": write_access,
                        },
                    },
                }
                async with self.client.context(cluster) as ctx:
                    async for event in ctx.pods(namespace):
                        yield event

        return gen()

    async def write_access(self, sccs_plugin, sccs_session, repo_name):
        permission = await self.sccs.get_repository_permission(sccs_plugin, sccs_session, repo_name)
        write_access = permission in ["admin", "write"] if permission is not None else False
        return write_access

    async def delete_pod(self, sccs_plugin, sccs_session, repository, environment, pod_name):

        if not await self.write_access(sccs_plugin, sccs_session, repository):
            raise AccessForbidden(f"You don't have write access on {repository} to delete a pod")

        namespace = self.repo_to_namespace(repository, environment)
        clusters = await self.get_pod_clusters(namespace)

        for cluster in clusters:
            async with self.client.context(cluster=cluster) as ctx:
                await ctx.delete_pod(pod_name, namespace)
