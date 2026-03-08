from __future__ import annotations

from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING

from app.schemas.business import BackMarketIntegrationConfig, BusinessBackMarketConfigResult


class BusinessRepository:
    """
    Repository for business documents and business-scoped integration config.

    Module 01 uses this for:
    - setup/bootstrap
    - business existence checks
    - Back Market integration config lookup
    """

    COLLECTION_NAME = "businesses"

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._database = database
        self._collection: AsyncIOMotorCollection = database[self.COLLECTION_NAME]

    async def ensure_indexes(self) -> None:
        """
        Create basic indexes required for bootstrap and business lookup.
        """
        await self._collection.create_index(
            [("_id", ASCENDING)],
            unique=True,
            name="uq_business_id",
        )

    async def count_businesses(self) -> int:
        """
        Return the total number of businesses in the system.
        """
        return await self._collection.count_documents({})

    async def get_by_id(self, business_id: str) -> dict | None:
        """
        Fetch a single business document by string `_id`.

        Returns the raw Mongo document or None if not found.
        """
        return await self._collection.find_one({"_id": business_id})

    async def get_backmarket_config(
        self,
        business_id: str,
    ) -> BusinessBackMarketConfigResult | None:
        """
        Fetch and validate the Back Market integration config for a business.

        Returns a typed result only when:
        - the business exists
        - integrations.backmarket exists

        It does not enforce `enabled=True` here. That belongs in the service layer.
        """
        business = await self.get_by_id(business_id)
        if business is None:
            return None

        integrations = business.get("integrations") or {}
        backmarket_raw = integrations.get("backmarket")
        if not backmarket_raw:
            return None

        config = BackMarketIntegrationConfig.model_validate(backmarket_raw)

        return BusinessBackMarketConfigResult(
            business_id=business["_id"],
            business_name=business.get("name", ""),
            config=config,
        )

    async def create_business(
        self,
        *,
        business_id: str,
        name: str,
        vat_registered: bool,
        vat_scheme: str | None,
        vat_period: str | None,
        vat_period_start,
        backmarket_config: dict,
    ) -> dict:
        """
        Create a business document with embedded Back Market integration config.
        """
        now = datetime.now(UTC)

        doc = {
            "_id": business_id,
            "name": name,
            "vat_registered": vat_registered,
            "vat_scheme": vat_scheme,
            "vat_period": vat_period,
            "vat_period_start": vat_period_start,
            "created_at": now,
            "updated_at": now,
            "integrations": {
                "backmarket": backmarket_config,
            },
        }

        await self._collection.insert_one(doc)
        return doc
