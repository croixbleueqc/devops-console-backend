from fastapi import APIRouter

from devops_console.clients import core

client = core.kubernetes

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


@router.get("/namespaces/{namespace}/status")
async def get_deployment_status(namespace: str, cluster: str | None = None):
    """Get pods."""
    return await client.get_deployment_status(namespace, cluster)
