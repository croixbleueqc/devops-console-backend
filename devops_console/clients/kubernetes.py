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

from anyio import create_task_group
from kubernetes_asyncio.client import V1Pod
from loguru import logger

from devops_console.k8s.client import K8sClient
from devops_console.sccs.errors import AccessForbidden
from ..clients.sccs import Sccs
from ..schemas.userconfig import KubernetesConfig


class Kubernetes(object):
    _instance = None
    client: K8sClient
    config: KubernetesConfig
    sccs: Sccs
    clusters: list[str]

    def __new__(cls, config: KubernetesConfig, sccs: Sccs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls.config = config
            cls.sccs = sccs
            # list cluster names on disk
            cls.clusters = os.listdir(cls.config.config_dir)
        return cls._instance

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

    async def pods_watch(
            self,
            sccs_plugin,
            sccs_session,
            repo_slug,
            environment,
            send_stream,
            cancel_event
            ):
        """Return a generator iterator of events for the pods of the given repository.
        see client.py in python-devops-kubernetes for the event shape.
        """

        namespace = self.repo_to_namespace(repo_slug, environment)

        pod_clusters = await self.get_pod_clusters(namespace)

        write_access = await self.write_access(sccs_plugin, sccs_session, repo_slug)

        if len(pod_clusters) == 0:
            logging.warning(f"No cluster found for namespace {namespace}.")
            return

        async def send_events():
            for cluster in pod_clusters:
                await send_stream.send(
                    {
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
                    )
                async with self.client.context(cluster) as ctx:
                    async for event in ctx.pods(namespace):
                        await send_stream.send(event)

        async with create_task_group() as tg:
            tg.start_soon(send_events)
            await cancel_event.wait()
            tg.cancel_scope.cancel()

    async def write_access(self, sccs_plugin, sccs_session, repo_slug):
        permission = await self.sccs.get_repository_permission(sccs_plugin, sccs_session, repo_slug)
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

    async def add_ns_to_exclude_from_kube_downscaler(
            self,
            namespaces: list[str],
            clusters: list[str] | None = None
            ):
        """Prevent selected namespaces from being automatically downscaled."""

        if len(namespaces) == 0:
            logger.warning("namespaces list is empty!")
            return

        if clusters is not None:
            if len(clusters) == 0:
                clusters = self.clusters
            else:
                # ensure clusters are valid
                if any(cluster not in self.clusters for cluster in clusters):
                    raise ValueError("Invalid cluster name")

        for cluster in clusters or self.clusters:
            async with self.client.context(cluster=cluster) as ctx:
                await ctx.add_ns_to_exclude_from_kube_downscaler(namespaces)

    async def remove_ns_to_exclude_from_kube_downscaler(
            self,
            namespaces: list[str],
            clusters: list[str] | None = None
            ):
        """Allow selected namespaces to be automatically downscaled."""

        if len(namespaces) == 0:
            logger.warning("namespaces list is empty!")
            return

        if clusters is not None:
            if len(clusters) == 0:
                clusters = self.clusters
            else:
                # ensure clusters are valid
                if any(cluster not in self.clusters for cluster in clusters):
                    raise ValueError("Invalid cluster name")

        for cluster in clusters or self.clusters:
            async with self.client.context(cluster=cluster) as ctx:
                await ctx.remove_ns_to_exclude_from_kube_downscaler(namespaces)

    async def get_deployment_status(self, namespace) -> dict[str, list[V1Pod]]:
        statuses = {}
        for cluster in await self.get_pod_clusters(namespace):
            async with self.client.context(cluster) as ctx:
                statuses[cluster] = await ctx.list_pods(namespace)
        return statuses
