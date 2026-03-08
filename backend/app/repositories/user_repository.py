from __future__ import annotations

from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING


class UserRepository:
    """
    Repository for the `users` collection.

    Module scope:
    - create a first bootstrap user
    - count users if needed later
    """

    COLLECTION_NAME = "users"

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._database = database
        self._collection: AsyncIOMotorCollection = database[self.COLLECTION_NAME]

    async def ensure_indexes(self) -> None:
        """
        Create basic indexes required for bootstrap and later user lookup.
        """
        await self._collection.create_index(
            [("_id", ASCENDING)],
            unique=True,
            name="uq_user_id",
        )
        await self._collection.create_index(
            [("business_id", ASCENDING), ("email", ASCENDING)],
            unique=True,
            name="uq_business_email",
        )

    async def create_user(
        self,
        *,
        user_id: str,
        business_id: str,
        name: str,
        email: str,
        role: str,
    ) -> dict:
        """
        Create a user document for the given business.
        """
        now = datetime.now(UTC)

        doc = {
            "_id": user_id,
            "business_id": business_id,
            "name": name,
            "email": email,
            "role": role,
            "active": True,
            "created_at": now,
            "updated_at": now,
        }

        await self._collection.insert_one(doc)
        return doc
