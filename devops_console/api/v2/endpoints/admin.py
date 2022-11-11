from fastapi import APIRouter, HTTPException

from devops_sccs.plugins.cache_keys import cache_key_fns
from devops_sccs.redis import RedisCache

cache = RedisCache()

router = APIRouter(prefix="/admin")


@router.delete("/cache/clear")
async def clear_cache(are_you_sure: bool = False):
    """Deletes ALL keys in the cache."""

    if not are_you_sure:
        raise HTTPException(
            status_code=400,
            detail="You must set the 'are_you_sure' query parameter to true to clear the cache."
            )

    try:
        await cache.clear()
        return {"message": "Cache cleared"}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear/by_function_signature/{function_name}")
async def clear_cache_key(
        function_name: str,
        args: tuple = (),
        kwargs: dict = None,
        ):
    """Deletes a key in the cache by function signature. The function must be registered in the
    cache_key_fns dictionary. If the function is not found it the dictionary, the function's name
    will be used as the key."""

    if kwargs is None:
        kwargs = {}

    if function_name in cache_key_fns:
        key = cache_key_fns[function_name](*args, **kwargs)
    else:
        key = function_name

    try:
        n = await cache.delete(key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if n > 0:
        return {"message": f"Cache key {key} cleared"}
    else:
        raise HTTPException(status_code=404, detail=f"Cache key {key} not found")


@router.delete("/cache/clear/by_namespace/{namespace}")
async def clear_cache_namespace(namespace: str):
    """Clear all cache keys with the given namespace. """

    try:
        n = await cache.delete_namespace(namespace)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if n > 0:
        return {"message": f"Cleared {n} keys in namespace {namespace}"}
    else:
        raise HTTPException(status_code=404, detail=f"Cache namespace {namespace} not found")
