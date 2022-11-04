from fastapi import APIRouter, HTTPException

from devops_sccs.plugins.cache_keys import cache_key_fns
from devops_sccs.redis import RedisCache

cache = RedisCache()

router = APIRouter(prefix="/admin")


@router.delete("/cache/clear")
async def clear_cache():
    try:
        await cache.clear()
        return {"message": "Cache cleared"}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear/by_key/")
async def clear_cache_key(
        name: str,
        args: tuple[str] = (),
        kwargs: dict = None,
        ):
    if kwargs is None:
        kwargs = {}

    # try to get the key from a cache key function
    if name in cache_key_fns:
        key = cache_key_fns[name](*args, **kwargs)
    # if there isn't a function by that name, just use the given name as the key
    else:
        key = name

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
    """Clear all cache keys with the given namespace.
    WARNING!!! This may be a very time-consuming operation, depending on the size of the cache.
    """

    try:
        n = await cache.delete_namespace(namespace)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if n > 0:
        return {"message": f"Cache namespace {namespace} cleared"}
    else:
        raise HTTPException(status_code=404, detail=f"Cache namespace {namespace} not found")
