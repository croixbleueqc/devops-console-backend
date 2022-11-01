from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/admin")


@router.get("/cache/clear")
async def clear_cache():
    from devops_sccs.redis import RedisCache
    cache = RedisCache()
    try:
        await cache.init()
        await cache.clear()
        return {"message": "Cache cleared"}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
