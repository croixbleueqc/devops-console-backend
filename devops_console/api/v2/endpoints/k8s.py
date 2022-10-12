from fastapi import APIRouter

from devops_console.clients import core

client = core.kubernetes

router = APIRouter()


@router.post("/no-dowscale")
async def exclude_namespaces_from_kube_downscaler(namespaces: list[str], clusters: list[str] | None = None):
    """Prevent selected namespaces from being automatically downscaled."""
    await client.add_ns_to_exclude_from_kube_downscaler(namespaces, clusters)
    return {"message": "success"}
