from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.db.collections import COLLECTIONS


class AuditRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self.database = database
        self.audit_logs = database[COLLECTIONS.audit_logs]
        self.businesses = database[COLLECTIONS.businesses]
        self.sites = database[COLLECTIONS.sites]

    async def insert_audit_log(self, *, document: dict[str, Any]) -> None:
        await self.audit_logs.insert_one(document)

    async def get_business_by_public_id(self, *, business_public_id: str) -> dict[str, Any] | None:
        return await self.businesses.find_one({"public_id": business_public_id})

    async def list_sites_for_business(self, *, business_public_id: str) -> list[dict[str, Any]]:
        cursor = self.sites.find({"business_id": business_public_id, "archived_at": None})
        return await cursor.to_list(length=None)

    async def list_business_events(
        self,
        *,
        business_public_id: str,
        limit: int,
        event_types: list[str] | None = None,
        before: datetime | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"business_id": business_public_id}
        if event_types:
            query["event_type"] = {"$in": event_types}
        if before is not None:
            query["created_at"] = {"$lt": before}
        cursor = self.audit_logs.find(query).sort("created_at", DESCENDING).limit(limit)
        return await cursor.to_list(length=limit)
