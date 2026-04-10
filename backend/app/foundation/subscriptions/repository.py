from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.db.collections import COLLECTIONS


class SubscriptionRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self.database = database
        self.businesses = database[COLLECTIONS.businesses]
        self.subscriptions = database[COLLECTIONS.subscriptions]
        self.subscription_history = database[COLLECTIONS.subscription_history]

    async def get_business_by_public_id(self, *, business_public_id: str) -> dict[str, Any] | None:
        return await self.businesses.find_one({"public_id": business_public_id})

    async def get_current_subscription_by_business_id(self, *, business_public_id: str) -> dict[str, Any] | None:
        return await self.subscriptions.find_one({"business_id": business_public_id})

    async def upsert_current_subscription(
        self,
        *,
        business_public_id: str,
        organisation_public_id: str,
        subscription_public_id: str,
        state: str,
        plan_code: str,
        billing_currency: str,
        billing_cadence: str,
        entitlements: dict[str, Any],
        created_at: datetime,
        updated_at: datetime,
    ) -> dict[str, Any]:
        existing = await self.get_current_subscription_by_business_id(business_public_id=business_public_id)
        if existing is None:
            document = {
                "public_id": subscription_public_id,
                "organisation_id": organisation_public_id,
                "business_id": business_public_id,
                "state": state,
                "plan_code": plan_code,
                "billing_currency": billing_currency,
                "billing_cadence": billing_cadence,
                "entitlements": entitlements,
                "created_at": created_at,
                "updated_at": updated_at,
            }
            await self.subscriptions.insert_one(document)
            return document

        await self.subscriptions.update_one(
            {"public_id": existing["public_id"]},
            {
                "$set": {
                    "state": state,
                    "plan_code": plan_code,
                    "billing_currency": billing_currency,
                    "billing_cadence": billing_cadence,
                    "entitlements": entitlements,
                    "updated_at": updated_at,
                }
            },
        )
        existing.update(
            {
                "state": state,
                "plan_code": plan_code,
                "billing_currency": billing_currency,
                "billing_cadence": billing_cadence,
                "entitlements": entitlements,
                "updated_at": updated_at,
            }
        )
        return existing

    async def mirror_site_capacity_to_business(
        self,
        *,
        business_public_id: str,
        included_site_limit: int,
        additional_site_slots: int,
        updated_at: datetime,
    ) -> None:
        await self.businesses.update_one(
            {"public_id": business_public_id},
            {
                "$set": {
                    "included_site_limit": included_site_limit,
                    "additional_site_slots": additional_site_slots,
                    "updated_at": updated_at,
                }
            },
        )

    async def append_subscription_history(
        self,
        *,
        public_id: str,
        subscription_public_id: str,
        organisation_id: str,
        business_id: str,
        state: str,
        plan_code: str,
        billing_currency: str,
        billing_cadence: str,
        entitlements: dict[str, Any],
        change_type: str,
        recorded_at: datetime,
    ) -> dict[str, Any]:
        document = {
            "public_id": public_id,
            "subscription_public_id": subscription_public_id,
            "organisation_id": organisation_id,
            "business_id": business_id,
            "state": state,
            "plan_code": plan_code,
            "billing_currency": billing_currency,
            "billing_cadence": billing_cadence,
            "entitlements": entitlements,
            "change_type": change_type,
            "recorded_at": recorded_at,
        }
        await self.subscription_history.insert_one(document)
        return document

    async def list_subscription_history_by_business_id(self, *, business_public_id: str) -> list[dict[str, Any]]:
        cursor = self.subscription_history.find({"business_id": business_public_id}).sort("recorded_at", -1)
        return [document async for document in cursor]


    async def update_business_state(
        self,
        *,
        business_public_id: str,
        state: str,
        updated_at: datetime,
    ) -> None:
        await self.businesses.update_one(
            {"public_id": business_public_id},
            {"$set": {"state": state, "updated_at": updated_at}},
        )
