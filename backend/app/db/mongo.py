from typing import Optional

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import get_settings


_client: Optional[AsyncMongoClient] = None


async def get_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncMongoClient(settings.mongo_uri)
    return _client


async def get_database() -> AsyncDatabase:
    settings = get_settings()
    client = await get_client()
    return client[settings.mongo_db_name]


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
