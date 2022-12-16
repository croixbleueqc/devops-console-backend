from typing import Literal

from fastapi import APIRouter, Depends
from kubernetes_asyncio.client import V1Pod
from pydantic import BaseModel

from devops_console.api.v2.dependencies import CommonHeaders
from devops_console.clients.client import CoreClient

client = CoreClient().kubernetes

router = APIRouter()


@router.post("/kube-downscaler")
async def add_ns_to_exclude_from_kube_downscaler(
        namespaces: list[str],
        clusters: list[str] | None = None
        ):
    """Prevent selected namespaces from being automatically downscaled."""
    await client.add_ns_to_exclude_from_kube_downscaler(namespaces, clusters)
    return {"message": "success"}


@router.delete("/kube-downscaler")
async def remove_ns_to_exclude_from_kube_downscaler(
        namespaces: list[str],
        clusters: list[str] | None = None
        ):
    """Allow selected namespaces to be automatically downscaled."""
    await client.remove_ns_to_exclude_from_kube_downscaler(namespaces, clusters)
    return {"message": "success"}


class ContainerStatus(BaseModel):
    name: str
    ready: bool
    restart_count: int


class PodStatus(BaseModel):
    name: str
    container_statuses: list[ContainerStatus]


class DeploymentStatus(BaseModel):
    cluster: str
    namespace: str
    permission: Literal["read", "write"]
    pods: list[PodStatus]


@router.get("/deployment-status/{repo_slug}/{environment}", response_model=list[DeploymentStatus])
async def get_deployment_status(
        repo_slug: str,
        environment: str,
        common_headers: CommonHeaders = Depends(),
        ):
    """Get statuses."""
    namespace = client.repo_to_namespace(repo_slug, environment)
    write_access = await client.write_access(
        common_headers.plugin_id,
        common_headers.credentials,
        repo_slug
        )
    permission = "write" if write_access else "read"

    deployment_status: dict[str, list[V1Pod]] = await client.get_deployment_status(namespace)

    result = []
    for cluster, pods in deployment_status.items():
        # noinspection PyTypeChecker
        result.append(
            DeploymentStatus(
                namespace=namespace,
                cluster=cluster,
                permission=permission,
                pods=[PodStatus(
                    name=pod.metadata.name,
                    container_statuses=[ContainerStatus(
                        name=container.name,
                        ready=container.ready,
                        restart_count=container.restart_count
                        ) for container in pod.status.container_statuses]
                    ) for pod in pods]
                )
            )
    return result
