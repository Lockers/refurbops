from __future__ import annotations

from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.db.collections import COLLECTIONS


class OrganisationRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self.organisations = database[COLLECTIONS.organisations]

    async def get_by_public_id(self, *, organisation_public_id: str) -> dict[str, Any] | None:
        return await self.organisations.find_one({"public_id": organisation_public_id})

    async def update_fields(self, *, organisation_public_id: str, update_fields: dict[str, Any]) -> None:
        await self.organisations.update_one(
            {"public_id": organisation_public_id},
            {"$set": update_fields},
        )
