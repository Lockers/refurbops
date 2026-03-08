from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.inbound_router import router as inbound_router
from app.api.routers.health import router as health_router
from app.core.config import get_settings
from app.core.database import close_client, get_database
from app.repositories.inbound_order_repository import InboundOrderRepository
from app.repositories.sync_state_repository import SyncStateRepository
from app.api.setup_router import router as setup_router
from app.repositories.business_repository import BusinessRepository
from app.repositories.user_repository import UserRepository

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application startup and shutdown lifecycle.

    Startup responsibilities:
    - Ensure MongoDB indexes required for inbound sync exist.

    Shutdown responsibilities:
    - Close the shared Motor client cleanly.
    """
    database: AsyncIOMotorDatabase = get_database()

    business_repo = BusinessRepository(database)
    user_repo = UserRepository(database)
    inbound_repo = InboundOrderRepository(database)
    sync_state_repo = SyncStateRepository(database)

    await business_repo.ensure_indexes()
    await user_repo.ensure_indexes()
    await inbound_repo.ensure_indexes()
    await sync_state_repo.ensure_indexes()

    yield

    await close_client()


api = FastAPI(
    title="RefurbOps API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(health_router)
api.include_router(inbound_router, prefix="/api/inbound", tags=["Inbound"])
api.include_router(setup_router, prefix="/api/setup", tags=["Setup"])


@api.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint returning basic API metadata.
    """
    return {
        "name": "refurbops-backend",
        "environment": settings.app_env,
        "status": "ready",
    }
