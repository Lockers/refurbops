from __future__ import annotations

from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING


class SyncStateRepository:
    """
    Repository for the `sync_states` collection.

    A sync state exists per business/source pair and stores the most recent
    attempt, success, and error information for incremental syncs.
    """

    COLLECTION_NAME = "sync_states"

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._database = database
        self._collection: AsyncIOMotorCollection = database[self.COLLECTION_NAME]

    async def ensure_indexes(self) -> None:
        """
        Create all MongoDB indexes required for Module 01 sync state tracking.
        """
        await self._collection.create_index(
            [("_id", ASCENDING)],
            unique=True,
            name="uq_sync_state_id",
        )
        await self._collection.create_index(
            [("business_id", ASCENDING), ("source", ASCENDING)],
            unique=True,
            name="uq_business_source",
        )

    async def get_sync_state(self, business_id: str, source: str) -> dict | None:
        """
        Fetch the sync state for a business/source pair.
        """
        return await self._collection.find_one(
            {
                "business_id": business_id,
                "source": source,
            }
        )

    async def record_attempt(self, business_id: str, source: str, attempted_at: datetime) -> None:
        """
        Record that a sync attempt has started.
        """
        await self._collection.update_one(
            {"_id": self._build_sync_state_id(business_id, source)},
            {
                "$set": {
                    "business_id": business_id,
                    "source": source,
                    "last_attempted_sync_at": attempted_at,
                    "updated_at": attempted_at,
                },
                "$setOnInsert": {
                    "last_successful_sync_at": None,
                    "last_full_resync_at": None,
                    "last_error": None,
                    "created_at": attempted_at,
                },
            },
            upsert=True,
        )

    async def record_success(
        self,
        business_id: str,
        source: str,
        attempted_at: datetime,
        successful_at: datetime,
    ) -> None:
        """
        Record a successful sync completion and clear the last error.
        """
        await self._collection.update_one(
            {"_id": self._build_sync_state_id(business_id, source)},
            {
                "$set": {
                    "business_id": business_id,
                    "source": source,
                    "last_attempted_sync_at": attempted_at,
                    "last_successful_sync_at": successful_at,
                    "last_error": None,
                    "updated_at": successful_at,
                },
                "$setOnInsert": {
                    "last_full_resync_at": None,
                    "created_at": attempted_at,
                },
            },
            upsert=True,
        )

    async def record_error(
        self,
        business_id: str,
        source: str,
        attempted_at: datetime,
        error_message: str,
    ) -> None:
        """
        Record a failed sync attempt.
        """
        await self._collection.update_one(
            {"_id": self._build_sync_state_id(business_id, source)},
            {
                "$set": {
                    "business_id": business_id,
                    "source": source,
                    "last_attempted_sync_at": attempted_at,
                    "last_error": error_message,
                    "updated_at": attempted_at,
                },
                "$setOnInsert": {
                    "last_successful_sync_at": None,
                    "last_full_resync_at": None,
                    "created_at": attempted_at,
                },
            },
            upsert=True,
        )

    @staticmethod
    def _build_sync_state_id(business_id: str, source: str) -> str:
        """
        Build the canonical sync state `_id`.

        Example:
            sync_backmarket_buyback_biz_001
        """
        return f"sync_{source}_{business_id}"
