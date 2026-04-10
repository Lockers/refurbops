from datetime import UTC, datetime
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.db.collections import COLLECTIONS
from app.foundation.users.models import UserDocument
from app.shared.utils.public_ids import new_public_id


class AuthRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self.database = database
        self.users = database[COLLECTIONS.users]
        self.credentials = database[COLLECTIONS.auth_credentials]
        self.auth_sessions = database[COLLECTIONS.auth_sessions]
        self.auth_refresh_tokens = database[COLLECTIONS.auth_refresh_tokens]
        self.user_invites = database[COLLECTIONS.user_invites]
        self.mfa_enrollments = database[COLLECTIONS.mfa_enrollments]
        self.mfa_recovery_codes = database[COLLECTIONS.mfa_recovery_codes]
        self.memberships = database[COLLECTIONS.memberships]
        self.businesses = database[COLLECTIONS.businesses]
        self.sites = database[COLLECTIONS.sites]

    async def list_platform_owner_users(self) -> list[dict[str, Any]]:
        cursor = self.users.find({"principal_type": "platform_owner"})
        return await cursor.to_list(length=10)

    async def get_user_by_email(self, *, email: str) -> dict[str, Any] | None:
        return await self.users.find_one({"email": email.lower().strip()})

    async def get_user_by_public_id(self, *, user_public_id: str) -> dict[str, Any] | None:
        return await self.users.find_one({"public_id": user_public_id})

    async def get_credentials_for_user(self, *, user_public_id: str) -> dict[str, Any] | None:
        return await self.credentials.find_one({"user_id": user_public_id})

    async def get_mfa_enrollment_for_user(self, *, user_public_id: str) -> dict[str, Any] | None:
        return await self.mfa_enrollments.find_one({"user_id": user_public_id})

    async def list_active_memberships_for_user(self, *, user_public_id: str) -> list[dict[str, Any]]:
        cursor = self.memberships.find({"user_id": user_public_id, "archived_at": None})
        return await cursor.to_list(length=200)


    async def get_businesses_by_public_ids(self, *, business_public_ids: list[str]) -> list[dict[str, Any]]:
        if not business_public_ids:
            return []
        cursor = self.businesses.find({"public_id": {"$in": business_public_ids}})
        return await cursor.to_list(length=len(business_public_ids))

    async def get_sites_by_public_ids(self, *, site_public_ids: list[str]) -> list[dict[str, Any]]:
        if not site_public_ids:
            return []
        cursor = self.sites.find({"public_id": {"$in": site_public_ids}, "state": {"$ne": "archived"}})
        return await cursor.to_list(length=len(site_public_ids))

    async def get_sites_for_business_ids(self, *, business_public_ids: list[str]) -> list[dict[str, Any]]:
        if not business_public_ids:
            return []
        cursor = self.sites.find({"business_id": {"$in": business_public_ids}, "state": {"$ne": "archived"}})
        return await cursor.to_list(length=500)

    async def get_active_session_by_public_id(self, *, session_public_id: str) -> dict[str, Any] | None:
        return await self.auth_sessions.find_one(
            {
                "public_id": session_public_id,
                "state": "active",
                "revoked_at": None,
            }
        )

    async def get_refresh_token_by_public_id(self, *, refresh_public_id: str) -> dict[str, Any] | None:
        return await self.auth_refresh_tokens.find_one({"public_id": refresh_public_id})

    async def touch_session(self, *, session_public_id: str, last_seen_at: datetime) -> None:
        await self.auth_sessions.update_one(
            {"public_id": session_public_id},
            {"$set": {"last_seen_at": last_seen_at, "updated_at": last_seen_at}},
        )

    async def refresh_session_idle_timeout(
        self,
        *,
        session_public_id: str,
        last_seen_at: datetime,
        idle_expires_at: datetime,
    ) -> None:
        await self.auth_sessions.update_one(
            {"public_id": session_public_id},
            {
                "$set": {
                    "last_seen_at": last_seen_at,
                    "idle_expires_at": idle_expires_at,
                    "updated_at": last_seen_at,
                }
            },
        )

    async def mark_session_reauthenticated(self, *, session_public_id: str, reauthenticated_at: datetime) -> None:
        await self.auth_sessions.update_one(
            {"public_id": session_public_id},
            {
                "$set": {
                    "reauthenticated_at": reauthenticated_at,
                    "updated_at": reauthenticated_at,
                }
            },
        )

    async def mark_refresh_token_consumed(self, *, refresh_public_id: str, consumed_at: datetime) -> None:
        await self.auth_refresh_tokens.update_one(
            {"public_id": refresh_public_id},
            {
                "$set": {
                    "state": "consumed",
                    "consumed_at": consumed_at,
                    "updated_at": consumed_at,
                }
            },
        )

    async def revoke_refresh_token(self, *, refresh_public_id: str, revoked_at: datetime) -> None:
        await self.auth_refresh_tokens.update_one(
            {"public_id": refresh_public_id},
            {
                "$set": {
                    "state": "revoked",
                    "revoked_at": revoked_at,
                    "updated_at": revoked_at,
                }
            },
        )

    async def revoke_refresh_family(self, *, family_id: str, revoked_at: datetime) -> None:
        await self.auth_refresh_tokens.update_many(
            {"family_id": family_id, "revoked_at": None},
            {
                "$set": {
                    "state": "revoked",
                    "revoked_at": revoked_at,
                    "updated_at": revoked_at,
                }
            },
        )

    async def revoke_session(self, *, session_public_id: str, revoked_at: datetime) -> None:
        await self.auth_sessions.update_one(
            {"public_id": session_public_id, "revoked_at": None},
            {
                "$set": {
                    "state": "revoked",
                    "revoked_at": revoked_at,
                    "updated_at": revoked_at,
                }
            },
        )

    async def get_invite_by_public_id(self, *, invite_public_id: str) -> dict[str, Any] | None:
        return await self.user_invites.find_one({"public_id": invite_public_id})

    async def get_pending_invite_for_user(self, *, user_public_id: str) -> dict[str, Any] | None:
        return await self.user_invites.find_one(
            {"user_id": user_public_id, "state": "pending", "revoked_at": None, "used_at": None}
        )

    async def revoke_pending_invites_for_user(self, *, user_public_id: str, revoked_at: datetime) -> int:
        result = await self.user_invites.update_many(
            {"user_id": user_public_id, "state": "pending", "revoked_at": None},
            {
                "$set": {
                    "state": "revoked",
                    "revoked_at": revoked_at,
                    "updated_at": revoked_at,
                }
            },
        )
        return int(result.modified_count)

    async def create_user_invite(
        self,
        *,
        user_public_id: str,
        email: str,
        organisation_id: str | None,
        token_hash: str,
        expires_at: datetime,
        issued_by_user_id: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        invite = {
            "public_id": new_public_id("inv"),
            "user_id": user_public_id,
            "email": email.lower().strip(),
            "organisation_id": organisation_id,
            "token_hash": token_hash,
            "state": "pending",
            "issued_by_user_id": issued_by_user_id,
            "expires_at": expires_at,
            "accepted_at": None,
            "used_at": None,
            "revoked_at": None,
            "created_at": now,
            "updated_at": now,
        }
        await self.user_invites.insert_one(invite)
        return invite

    async def accept_user_invite(self, *, invite_public_id: str, accepted_at: datetime) -> None:
        await self.user_invites.update_one(
            {"public_id": invite_public_id},
            {
                "$set": {
                    "state": "accepted",
                    "accepted_at": accepted_at,
                    "used_at": accepted_at,
                    "updated_at": accepted_at,
                }
            },
        )

    async def activate_tenant_user(self, *, user_public_id: str) -> None:
        now = datetime.now(UTC)
        await self.users.update_one(
            {"public_id": user_public_id},
            {
                "$set": {
                    "state": "active",
                    "password_change_required": False,
                    "updated_at": now,
                }
            },
        )

    async def create_platform_owner(
        self,
        *,
        email: str,
        password_hash: str,
        mfa_required: bool,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        user = UserDocument(
            public_id=new_public_id("usr"),
            email=email.lower().strip(),
            principal_type="platform_owner",
            organisation_id=None,
            state="active",
            display_name="Platform Owner",
            password_change_required=True,
            mfa_required=mfa_required,
            created_at=now,
            updated_at=now,
        ).model_dump(mode="json")

        await self.users.insert_one(user)
        try:
            await self.create_local_password_credentials(
                user_public_id=user["public_id"],
                password_hash=password_hash,
            )
        except Exception:
            await self.users.delete_one({"public_id": user["public_id"]})
            raise

        return user

    async def create_local_password_credentials(
        self,
        *,
        user_public_id: str,
        password_hash: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        credential = {
            "public_id": new_public_id("cred"),
            "user_id": user_public_id,
            "scheme": "argon2id",
            "password_hash": password_hash,
            "password_set_at": now,
            "created_at": now,
            "updated_at": now,
        }
        await self.credentials.insert_one(credential)
        return credential

    async def update_local_password_credentials(
        self,
        *,
        user_public_id: str,
        password_hash: str,
    ) -> None:
        now = datetime.now(UTC)
        await self.credentials.update_one(
            {"user_id": user_public_id},
            {
                "$set": {
                    "scheme": "argon2id",
                    "password_hash": password_hash,
                    "password_set_at": now,
                    "updated_at": now,
                }
            },
        )

    async def clear_password_change_required(self, *, user_public_id: str) -> None:
        now = datetime.now(UTC)
        await self.users.update_one(
            {"public_id": user_public_id},
            {
                "$set": {
                    "password_change_required": False,
                    "updated_at": now,
                }
            },
        )

    async def start_mfa_enrollment(
        self,
        *,
        user_public_id: str,
        secret: str,
        provisioning_uri: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        enrollment = {
            "public_id": new_public_id("mfa"),
            "user_id": user_public_id,
            "method": "totp",
            "status": "pending_verification",
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "verified_at": None,
            "created_at": now,
            "updated_at": now,
        }
        await self.mfa_enrollments.update_one(
            {"user_id": user_public_id},
            {"$set": enrollment},
            upsert=True,
        )
        return enrollment

    async def complete_mfa_enrollment(self, *, user_public_id: str) -> None:
        now = datetime.now(UTC)
        await self.mfa_enrollments.update_one(
            {"user_id": user_public_id},
            {
                "$set": {
                    "status": "active",
                    "verified_at": now,
                    "updated_at": now,
                    "provisioning_uri": None,
                }
            },
        )

    async def replace_recovery_codes(
        self,
        *,
        user_public_id: str,
        code_hashes: list[str],
    ) -> None:
        now = datetime.now(UTC)
        await self.mfa_recovery_codes.delete_many({"user_id": user_public_id})
        if not code_hashes:
            return

        documents = [
            {
                "public_id": new_public_id("mrc"),
                "user_id": user_public_id,
                "code_hash": code_hash,
                "used_at": None,
                "created_at": now,
                "updated_at": now,
            }
            for code_hash in code_hashes
        ]
        await self.mfa_recovery_codes.insert_many(documents)

    async def create_auth_session(
        self,
        *,
        user: dict[str, Any],
        mfa_verified_at: datetime,
        idle_expires_at: datetime,
        absolute_expires_at: datetime,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        refresh_family_id = new_public_id("srf")
        session = {
            "public_id": new_public_id("ses"),
            "user_id": user["public_id"],
            "user_email": user["email"],
            "principal_type": user["principal_type"],
            "state": "active",
            "mfa_verified_at": mfa_verified_at,
            "reauthenticated_at": mfa_verified_at,
            "last_seen_at": now,
            "idle_expires_at": idle_expires_at,
            "absolute_expires_at": absolute_expires_at,
            "refresh_family_id": refresh_family_id,
            "revoked_at": None,
            "created_at": now,
            "updated_at": now,
        }
        await self.auth_sessions.insert_one(session)
        return session

    async def create_refresh_token_record(
        self,
        *,
        session_public_id: str,
        user_public_id: str,
        family_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        refresh_record = {
            "public_id": new_public_id("rft"),
            "session_id": session_public_id,
            "user_id": user_public_id,
            "family_id": family_id,
            "token_hash": token_hash,
            "state": "active",
            "issued_at": now,
            "expires_at": expires_at,
            "consumed_at": None,
            "revoked_at": None,
            "created_at": now,
            "updated_at": now,
        }
        await self.auth_refresh_tokens.insert_one(refresh_record)
        return refresh_record

    async def get_businesses_by_public_ids(self, *, business_public_ids: list[str]) -> list[dict[str, Any]]:
        if not business_public_ids:
            return []
        cursor = self.database[COLLECTIONS.businesses].find(
            {"public_id": {"$in": business_public_ids}}
        )
        return await cursor.to_list(length=len(business_public_ids))

    async def get_sites_by_public_ids(self, *, site_public_ids: list[str]) -> list[dict[str, Any]]:
        if not site_public_ids:
            return []
        cursor = self.database[COLLECTIONS.sites].find(
            {"public_id": {"$in": site_public_ids}}
        )
        return await cursor.to_list(length=len(site_public_ids))

    async def get_sites_for_business_ids(self, *, business_public_ids: list[str]) -> list[dict[str, Any]]:
        if not business_public_ids:
            return []
        cursor = self.database[COLLECTIONS.sites].find(
            {"business_id": {"$in": business_public_ids}}
        )
        return await cursor.to_list(length=500)

