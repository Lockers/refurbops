from __future__ import annotations

"""
Async MongoDB connection management for RefurbOps.

Why Motor now:
- FastAPI is async-friendly
- Back Market client will be async
- inbound sync and later modules will involve many I/O-bound operations
- switching later would create avoidable churn in repositories/services

This module exposes:
- get_client() -> AsyncIOMotorClient
- get_database() -> AsyncIOMotorDatabase
- close_client() -> None

The rest of the backend should depend on get_database() and keep all Mongo
collection access inside repositories.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    """
    Return a singleton Motor client for the application process.

    The client is created lazily on first use and then reused for all requests.
    """
    global _client

    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongo_uri)

    return _client


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the configured MongoDB database instance.

    The database name comes from application settings.
    """
    settings = get_settings()
    return get_client()[settings.mongo_db_name]


async def close_client() -> None:
    """
    Close the MongoDB client cleanly.

    This should be called during FastAPI shutdown so connections are released
    properly when the app stops or reloads.
    """
    global _client

    if _client is not None:
        _client.close()
        _client = None
