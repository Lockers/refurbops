from __future__ import annotations

from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.db.collections import COLLECTIONS


class SiteRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self.sites = database[COLLECTIONS.sites]
        self.businesses = database[COLLECTIONS.businesses]

    async def get_site_by_public_id(self, *, site_public_id: str) -> dict[str, Any] | None:
        return await self.sites.find_one({"public_id": site_public_id})

    async def get_business_by_public_id(self, *, business_public_id: str) -> dict[str, Any] | None:
        return await self.businesses.find_one({"public_id": business_public_id})

    async def list_sites_for_business(self, *, business_public_id: str) -> list[dict[str, Any]]:
        cursor = self.sites.find({"business_id": business_public_id}).sort("created_at", 1)
        return [document async for document in cursor]

    async def update_site_fields(self, *, site_public_id: str, update_fields: dict[str, Any]) -> None:
        await self.sites.update_one(
            {"public_id": site_public_id},
            {"$set": update_fields},
        )
