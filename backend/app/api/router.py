from fastapi import APIRouter, HTTPException, status

from app.audit.router import audit_router
from app.auth.router import auth_router
from app.db.mongo import get_database
from app.db.redis import get_redis
from app.foundation.businesses.router import businesses_router
from app.foundation.organisations.router import organisations_router
from app.foundation.sites.router import sites_router
from app.foundation.subscriptions.router import subscriptions_router


api_router = APIRouter()


@api_router.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@api_router.get("/health/ready", tags=["health"])
async def readiness() -> dict[str, str]:
    try:
        database = await get_database()
        await database.command({"ping": 1})
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not ready") from exc

    try:
        redis = await get_redis()
        await redis.ping()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis not ready") from exc

    return {"status": "ready"}


api_router.include_router(auth_router)
api_router.include_router(audit_router)
api_router.include_router(organisations_router)
api_router.include_router(businesses_router)
api_router.include_router(sites_router)
api_router.include_router(subscriptions_router)
