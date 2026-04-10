from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.correlation_id import CorrelationIdMiddleware
from app.api.router import api_router
from app.bootstrap.platform_owner import ensure_platform_owner_seeded
from app.config import get_settings
from app.db.indexes import ensure_indexes
from app.db.mongo import close_client, get_database
from app.db.redis import close_redis, get_redis
from app.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings=settings)

    database = await get_database()
    app.state.mongo_db = database
    await ensure_indexes(database)
    await ensure_platform_owner_seeded(database=database, settings=settings)

    redis = await get_redis()
    app.state.redis = redis

    yield

    await close_redis()
    await close_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
