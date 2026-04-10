from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.db.collections import COLLECTIONS


class BusinessProvisioningRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self.database = database
        self.organisations = database[COLLECTIONS.organisations]
        self.businesses = database[COLLECTIONS.businesses]
        self.sites = database[COLLECTIONS.sites]
        self.users = database[COLLECTIONS.users]
        self.memberships = database[COLLECTIONS.memberships]
        self.subscriptions = database[COLLECTIONS.subscriptions]
        self.auth_sessions = database[COLLECTIONS.auth_sessions]
        self.auth_refresh_tokens = database[COLLECTIONS.auth_refresh_tokens]

    async def get_user_by_email(self, *, email: str) -> dict[str, Any] | None:
        return await self.users.find_one({"email": email.lower().strip()})

    async def get_user_by_public_id(self, *, user_public_id: str) -> dict[str, Any] | None:
        return await self.users.find_one({"public_id": user_public_id})

    async def get_business_by_public_id(self, *, business_public_id: str) -> dict[str, Any] | None:
        return await self.businesses.find_one({"public_id": business_public_id})

    async def update_business_fields(
        self,
        *,
        business_public_id: str,
        update_fields: dict[str, Any],
    ) -> None:
        await self.businesses.update_one(
            {"public_id": business_public_id},
            {"$set": update_fields},
        )

    async def get_site_by_public_id(self, *, site_public_id: str) -> dict[str, Any] | None:
        return await self.sites.find_one({"public_id": site_public_id})

    async def list_sites_for_business(self, *, business_public_id: str) -> list[dict[str, Any]]:
        cursor = self.sites.find({"business_id": business_public_id}).sort("created_at", 1)
        return [document async for document in cursor]

    async def count_non_archived_sites_for_business(self, *, business_public_id: str) -> int:
        return await self.sites.count_documents({"business_id": business_public_id, "state": {"$ne": "archived"}})

    async def list_memberships_applicable_to_business(
        self,
        *,
        organisation_public_id: str,
        business_public_id: str,
        site_public_ids: list[str],
    ) -> list[dict[str, Any]]:
        membership_filter: dict[str, Any] = {
            "organisation_id": organisation_public_id,
            "archived_at": None,
            "$or": [
                {"scope_type": "organisation", "scope_id": organisation_public_id},
                {"scope_type": "business", "scope_id": business_public_id},
            ],
        }
        if site_public_ids:
            membership_filter["$or"].append({"scope_type": "site", "scope_id": {"$in": site_public_ids}})

        cursor = self.memberships.find(membership_filter).sort([("role", 1), ("created_at", 1)])
        memberships = [document async for document in cursor]
        if not memberships:
            return []

        user_public_ids = [str(document.get("user_id", "")) for document in memberships if document.get("user_id")]
        users_by_public_id: dict[str, dict[str, Any]] = {}
        if user_public_ids:
            user_cursor = self.users.find({"public_id": {"$in": user_public_ids}})
            users_by_public_id = {
                str(document["public_id"]): document
                async for document in user_cursor
            }

        result: list[dict[str, Any]] = []
        for membership in memberships:
            combined = dict(membership)
            combined["user"] = users_by_public_id.get(str(membership.get("user_id", "")))
            result.append(combined)
        return result

    async def get_membership_by_public_id(self, *, membership_public_id: str) -> dict[str, Any] | None:
        return await self.memberships.find_one({"public_id": membership_public_id})

    async def get_membership_with_user_by_public_id(self, *, membership_public_id: str) -> dict[str, Any] | None:
        membership = await self.get_membership_by_public_id(membership_public_id=membership_public_id)
        if membership is None:
            return None
        user = await self.get_user_by_public_id(user_public_id=str(membership.get("user_id", "")))
        combined = dict(membership)
        combined["user"] = user
        return combined

    async def count_active_business_owner_memberships(self, *, business_public_id: str) -> int:
        return await self.memberships.count_documents({
            "scope_type": "business",
            "scope_id": business_public_id,
            "role": "business_owner",
            "archived_at": None,
        })


    async def list_active_memberships_for_user_applicable_to_business(
        self,
        *,
        user_public_id: str,
        organisation_public_id: str,
        business_public_id: str,
        site_public_ids: list[str],
    ) -> list[dict[str, Any]]:
        membership_filter: dict[str, Any] = {
            "user_id": user_public_id,
            "organisation_id": organisation_public_id,
            "archived_at": None,
            "$or": [
                {"scope_type": "organisation", "scope_id": organisation_public_id},
                {"scope_type": "business", "scope_id": business_public_id},
            ],
        }
        if site_public_ids:
            membership_filter["$or"].append({"scope_type": "site", "scope_id": {"$in": site_public_ids}})

        cursor = self.memberships.find(membership_filter)
        return [document async for document in cursor]

    async def set_user_state(
        self,
        *,
        user_public_id: str,
        state: str,
        updated_at: datetime,
        suspension_restore_state: str | None = None,
    ) -> None:
        update_fields: dict[str, Any] = {
            "state": state,
            "updated_at": updated_at,
        }
        if suspension_restore_state is None:
            update_fields["suspension_restore_state"] = None
        else:
            update_fields["suspension_restore_state"] = suspension_restore_state

        await self.users.update_one(
            {"public_id": user_public_id},
            {"$set": update_fields},
        )

    async def revoke_sessions_for_user(
        self,
        *,
        user_public_id: str,
        revoked_at: datetime,
    ) -> tuple[int, int]:
        sessions_result = await self.auth_sessions.update_many(
            {"user_id": user_public_id, "revoked_at": None},
            {
                "$set": {
                    "state": "revoked",
                    "revoked_at": revoked_at,
                    "updated_at": revoked_at,
                }
            },
        )
        refresh_result = await self.auth_refresh_tokens.update_many(
            {"user_id": user_public_id, "revoked_at": None},
            {
                "$set": {
                    "state": "revoked",
                    "revoked_at": revoked_at,
                    "updated_at": revoked_at,
                }
            },
        )
        return sessions_result.modified_count, refresh_result.modified_count

    async def archive_membership(self, *, membership_public_id: str, archived_at: datetime, updated_at: datetime) -> None:
        await self.memberships.update_one(
            {"public_id": membership_public_id},
            {"$set": {"archived_at": archived_at, "updated_at": updated_at}},
        )

    async def find_active_membership(
        self,
        *,
        user_public_id: str,
        scope_type: str,
        scope_id: str,
        role: str,
    ) -> dict[str, Any] | None:
        return await self.memberships.find_one(
            {
                "user_id": user_public_id,
                "scope_type": scope_type,
                "scope_id": scope_id,
                "role": role,
                "archived_at": None,
            }
        )




    async def get_current_subscription_by_business_id(self, *, business_public_id: str) -> dict[str, Any] | None:
        return await self.subscriptions.find_one({"business_id": business_public_id})

    async def update_subscription_site_capacity(
        self,
        *,
        business_public_id: str,
        additional_site_slots: int,
        included_site_limit: int | None = None,
        updated_at: datetime,
    ) -> None:
        subscription = await self.get_current_subscription_by_business_id(business_public_id=business_public_id)
        if subscription is None:
            return

        entitlements = dict(subscription.get("entitlements", {}))
        entitlements["additional_site_slots"] = additional_site_slots
        if included_site_limit is not None:
            entitlements["included_site_limit"] = included_site_limit

        await self.subscriptions.update_one(
            {"public_id": subscription["public_id"]},
            {"$set": {"entitlements": entitlements, "updated_at": updated_at}},
        )

    async def update_business_site_capacity(
        self,
        *,
        business_public_id: str,
        additional_site_slots: int,
        updated_at: datetime,
    ) -> None:
        await self.businesses.update_one(
            {"public_id": business_public_id},
            {"$set": {"additional_site_slots": additional_site_slots, "updated_at": updated_at}},
        )



    async def count_active_sites_for_business(self, *, business_public_id: str) -> int:
        return await self.sites.count_documents({"business_id": business_public_id, "state": "active"})

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

    async def insert_organisation(self, document: dict[str, Any]) -> None:
        await self.organisations.insert_one(document)

    async def insert_business(self, document: dict[str, Any]) -> None:
        await self.businesses.insert_one(document)

    async def insert_site(self, document: dict[str, Any]) -> None:
        await self.sites.insert_one(document)

    async def insert_user(self, document: dict[str, Any]) -> None:
        await self.users.insert_one(document)

    async def insert_membership(self, document: dict[str, Any]) -> None:
        await self.memberships.insert_one(document)

    async def rollback_created_documents(self, *, public_ids: Iterable[tuple[str, str]]) -> None:
        for collection_name, public_id in public_ids:
            await self.database[collection_name].delete_one({"public_id": public_id})


    async def set_site_state(
        self,
        *,
        site_public_id: str,
        state: str,
        updated_at: datetime,
    ) -> None:
        await self.sites.update_one(
            {"public_id": site_public_id},
            {"$set": {"state": state, "updated_at": updated_at}},
        )

