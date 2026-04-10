from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.auth.schemas import AuthenticatedRequestContext
from app.auth.service import auth_service
from app.audit.schemas import AuditEventCreate
from app.audit.service import audit_service
from app.db.collections import COLLECTIONS
from app.foundation.businesses.models import BusinessDocument
from app.foundation.businesses.repository import BusinessProvisioningRepository
from app.foundation.businesses.schemas import (
    BusinessMembershipCreateRequest,
    BusinessMembershipArchiveResponse,
    BusinessMembershipCreateResponse,
    BusinessMembershipsReadResponse,
    BusinessReadResponse,
    BusinessUpdateRequest,
    BusinessUpdateResponse,
    BusinessReference,
    BusinessSiteCreateRequest,
    BusinessSiteCreateResponse,
    BusinessSiteCapacityUpdateRequest,
    BusinessSiteCapacityUpdateResponse,
    BusinessSitesReadResponse,
    BusinessActivationChecks,
    BusinessActivateResponse,
    BusinessUserSuspendResponse,
    BusinessUserReactivateResponse,
    BusinessView,
    CreatedEntityReference,
    MembershipUserSummary,
    MembershipView,
    ProvisionInitialBusinessRequest,
    ProvisionInitialBusinessResponse,
    ProvisionedBusinessOwnerUser,
    ProvisionedMembershipReference,
    SiteCapacitySummary,
    SiteView,
)
from app.foundation.memberships.models import MembershipDocument
from app.foundation.organisations.models import OrganisationDocument
from app.foundation.sites.models import SiteDocument
from app.foundation.users.models import UserDocument
from app.shared.utils.public_ids import new_public_id


def _conflict_detail(message: str, reason_code: str) -> dict[str, str]:
    return {"message": message, "reason_code": reason_code}


class BusinessProvisioningService:
    @staticmethod
    def _coerce_iso(value: Any) -> str:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.isoformat()
        return str(value)

    @staticmethod
    def _coerce_utc(value: Any) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        raise TypeError(f"Unsupported datetime value: {value!r}")

    @staticmethod
    def _user_summary(user: dict[str, Any]) -> MembershipUserSummary:
        return MembershipUserSummary(
            public_id=str(user["public_id"]),
            email=str(user["email"]),
            display_name=user.get("display_name"),
            state=str(user.get("state", "")),
            principal_type=str(user.get("principal_type", "")),
        )

    def _build_business_view(self, document: dict[str, Any]) -> BusinessView:
        return BusinessView(
            public_id=str(document["public_id"]),
            organisation_id=str(document["organisation_id"]),
            name=str(document["name"]),
            state=str(document["state"]),
            timezone=str(document["timezone"]),
            country_code=str(document["country_code"]),
            currency_code=str(document["currency_code"]),
            locale=str(document["locale"]),
            language=str(document["language"]),
            created_at=self._coerce_iso(document["created_at"]),
            updated_at=self._coerce_iso(document["updated_at"]),
        )

    def _build_site_view(self, document: dict[str, Any]) -> SiteView:
        return SiteView(
            public_id=str(document["public_id"]),
            organisation_id=str(document["organisation_id"]),
            business_id=str(document["business_id"]),
            name=str(document["name"]),
            state=str(document["state"]),
            timezone=document.get("timezone"),
            locale=document.get("locale"),
            language=document.get("language"),
            created_at=self._coerce_iso(document["created_at"]),
            updated_at=self._coerce_iso(document["updated_at"]),
        )

    @staticmethod
    def _coerce_positive_int(value: Any, *, minimum: int, fallback: int) -> int:
        try:
            return max(minimum, int(value))
        except (TypeError, ValueError):
            return fallback

    def _site_capacity_inputs(
        self,
        *,
        business: dict[str, Any],
        subscription: dict[str, Any] | None,
    ) -> tuple[int, int]:
        entitlements = dict((subscription or {}).get("entitlements", {}))
        included_site_limit = self._coerce_positive_int(
            entitlements.get("included_site_limit", business.get("included_site_limit", 1)),
            minimum=1,
            fallback=1,
        )
        additional_site_slots = self._coerce_positive_int(
            entitlements.get("additional_site_slots", business.get("additional_site_slots", 0)),
            minimum=0,
            fallback=0,
        )
        return included_site_limit, additional_site_slots

    def _build_site_capacity_summary(
        self,
        *,
        business: dict[str, Any],
        subscription: dict[str, Any] | None,
        current_non_archived_site_count: int,
    ) -> SiteCapacitySummary:
        included_site_limit, additional_site_slots = self._site_capacity_inputs(
            business=business,
            subscription=subscription,
        )
        effective_site_limit = included_site_limit + additional_site_slots
        remaining_site_capacity = max(0, effective_site_limit - current_non_archived_site_count)
        return SiteCapacitySummary(
            included_site_limit=included_site_limit,
            additional_site_slots=additional_site_slots,
            effective_site_limit=effective_site_limit,
            current_non_archived_site_count=current_non_archived_site_count,
            remaining_site_capacity=remaining_site_capacity,
        )

    @staticmethod
    def _ensure_business_allows_site_creation(*, business: dict[str, Any]) -> None:
        business_state = str(business.get("state", ""))
        if business_state in {"pending_setup", "active"}:
            return
        if business_state == "read_only":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Cannot create sites while business is read_only", "business_read_only"))
        if business_state == "suspended":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Cannot create sites while business is suspended", "business_suspended"))
        if business_state == "archived":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Cannot create sites for an archived business", "business_archived"))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Business does not allow site creation", "business_state_blocked"))

    @staticmethod
    def _ensure_business_allows_membership_mutation(*, business: dict[str, Any]) -> None:
        business_state = str(business.get("state", ""))
        if business_state in {"pending_setup", "active"}:
            return
        if business_state == "read_only":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Cannot modify memberships while business is read_only", "business_read_only"))
        if business_state == "suspended":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Cannot modify memberships while business is suspended", "business_suspended"))
        if business_state == "archived":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Cannot modify memberships for an archived business", "business_archived"))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Business does not allow membership changes", "business_state_blocked"))

    def _build_membership_view(self, document: dict[str, Any]) -> MembershipView:
        user = document.get("user") or {}
        return MembershipView(
            public_id=str(document["public_id"]),
            role=str(document["role"]),
            scope_type=str(document["scope_type"]),
            scope_id=str(document["scope_id"]),
            user=self._user_summary(user),
            archived_at=self._coerce_iso(document["archived_at"]) if document.get("archived_at") else None,
            created_at=self._coerce_iso(document["created_at"]),
            updated_at=self._coerce_iso(document["updated_at"]),
        )

    @staticmethod
    def _principal_type(context: AuthenticatedRequestContext) -> str:
        return str(context.user.get("principal_type", "")).strip()

    def _ensure_business_access(
        self,
        *,
        context: AuthenticatedRequestContext,
        business: dict[str, Any],
        site_public_ids: list[str],
    ) -> None:
        if self._principal_type(context) == "platform_owner":
            return

        business_public_id = str(business["public_id"])
        organisation_public_id = str(business["organisation_id"])
        for membership in context.memberships:
            if str(membership.get("organisation_id", "")) != organisation_public_id:
                continue
            scope_type = str(membership.get("scope_type", ""))
            scope_id = str(membership.get("scope_id", ""))
            if scope_type == "organisation" and scope_id == organisation_public_id:
                return
            if scope_type == "business" and scope_id == business_public_id:
                return
            if scope_type == "site" and scope_id in site_public_ids:
                return

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Business is outside your allowed scope")

    async def provision_initial_business(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        payload: ProvisionInitialBusinessRequest,
    ) -> ProvisionInitialBusinessResponse:
        repository = BusinessProvisioningRepository(database)
        await auth_service.require_fresh_reauthentication(
            database=database,
            context=context,
            action="foundation.business.provision_initial",
        )

        existing_user = await repository.get_user_by_email(email=payload.business_owner_email)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Business owner email already exists",
            )

        organisation = OrganisationDocument(
            public_id=new_public_id("org"),
            name=payload.organisation_name.strip(),
        ).model_dump(mode="json")
        business = BusinessDocument(
            public_id=new_public_id("bus"),
            organisation_id=organisation["public_id"],
            name=payload.business_name.strip(),
        ).model_dump(mode="json")
        site = SiteDocument(
            public_id=new_public_id("site"),
            organisation_id=organisation["public_id"],
            business_id=business["public_id"],
            name=payload.primary_site_name.strip(),
            timezone=business["timezone"],
            locale=business["locale"],
            language=business["language"],
        ).model_dump(mode="json")
        business_owner_user = UserDocument(
            public_id=new_public_id("usr"),
            email=payload.business_owner_email.lower().strip(),
            principal_type="tenant_user",
            organisation_id=organisation["public_id"],
            state="pending_activation",
            display_name=payload.business_owner_display_name.strip(),
            password_change_required=True,
            mfa_required=True,
        ).model_dump(mode="json")
        business_owner_membership = MembershipDocument(
            public_id=new_public_id("mbr"),
            user_id=business_owner_user["public_id"],
            organisation_id=organisation["public_id"],
            scope_type="business",
            scope_id=business["public_id"],
            role="business_owner",
        ).model_dump(mode="json")

        created: list[tuple[str, str]] = []
        try:
            await repository.insert_organisation(organisation)
            created.append((COLLECTIONS.organisations, organisation["public_id"]))
            await repository.insert_business(business)
            created.append((COLLECTIONS.businesses, business["public_id"]))
            await repository.insert_site(site)
            created.append((COLLECTIONS.sites, site["public_id"]))
            await repository.insert_user(business_owner_user)
            created.append((COLLECTIONS.users, business_owner_user["public_id"]))
            await repository.insert_membership(business_owner_membership)
            created.append((COLLECTIONS.memberships, business_owner_membership["public_id"]))
        except Exception:
            await repository.rollback_created_documents(public_ids=reversed(created))
            raise

        actor = audit_service.actor_from_context(context)
        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.organisation.created",
                entity_type="organisation",
                entity_public_id=organisation["public_id"],
                organisation_public_id=organisation["public_id"],
                actor=actor,
                metadata={"name": organisation["name"]},
            ),
        )
        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.business.created",
                entity_type="business",
                entity_public_id=business["public_id"],
                organisation_public_id=organisation["public_id"],
                business_public_id=business["public_id"],
                actor=actor,
                metadata={
                    "name": business["name"],
                    "state": business["state"],
                },
            ),
        )
        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.site.created",
                entity_type="site",
                entity_public_id=site["public_id"],
                organisation_public_id=organisation["public_id"],
                business_public_id=business["public_id"],
                site_public_id=site["public_id"],
                actor=actor,
                metadata={
                    "name": site["name"],
                    "state": site["state"],
                    "initial_site": True,
                },
            ),
        )

        return ProvisionInitialBusinessResponse(
            organisation=CreatedEntityReference(public_id=organisation["public_id"], name=organisation["name"]),
            business=CreatedEntityReference(public_id=business["public_id"], name=business["name"]),
            primary_site=CreatedEntityReference(public_id=site["public_id"], name=site["name"]),
            business_owner_user=ProvisionedBusinessOwnerUser(
                public_id=business_owner_user["public_id"],
                email=business_owner_user["email"],
                display_name=business_owner_user["display_name"],
                state=business_owner_user["state"],
                principal_type=business_owner_user["principal_type"],
            ),
            business_owner_membership=ProvisionedMembershipReference(
                public_id=business_owner_membership["public_id"],
                role=business_owner_membership["role"],
                scope_type=business_owner_membership["scope_type"],
                scope_id=business_owner_membership["scope_id"],
            ),
        )

    async def get_business(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
    ) -> BusinessReadResponse:
        repository = BusinessProvisioningRepository(database)
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site["public_id"]) for site in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)

        return BusinessReadResponse(business=self._build_business_view(business))

    async def update_business(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
        payload: BusinessUpdateRequest,
    ) -> BusinessUpdateResponse:
        repository = BusinessProvisioningRepository(database)
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site["public_id"]) for site in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)

        payload_data = payload.model_dump(exclude_unset=True)
        if not payload_data:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one field must be provided")

        updates: dict[str, Any] = {}
        changes: dict[str, dict[str, str]] = {}

        for field_name, raw_value in payload_data.items():
            if raw_value is None:
                continue
            if isinstance(raw_value, str):
                new_value = raw_value.strip()
                if field_name == "country_code":
                    new_value = new_value.upper()
                if field_name == "currency_code":
                    new_value = new_value.upper()
            else:
                new_value = raw_value

            old_value = business.get(field_name)
            if old_value == new_value:
                continue

            updates[field_name] = new_value
            changes[field_name] = {
                "before": "" if old_value is None else str(old_value),
                "after": "" if new_value is None else str(new_value),
            }

        if not updates:
            return BusinessUpdateResponse(business=self._build_business_view(business))

        updated_at = datetime.now(UTC)
        updates["updated_at"] = updated_at
        await repository.update_business_fields(
            business_public_id=business_public_id,
            update_fields=updates,
        )

        refreshed = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.business.updated",
                entity_type="business",
                entity_public_id=str(refreshed["public_id"]),
                organisation_public_id=str(refreshed["organisation_id"]),
                business_public_id=str(refreshed["public_id"]),
                actor=audit_service.actor_from_context(context),
                metadata={
                    "updated_fields": sorted(changes.keys()),
                    "changes": changes,
                },
                created_at=updated_at,
            ),
        )

        return BusinessUpdateResponse(business=self._build_business_view(refreshed))

    async def list_business_sites(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
    ) -> BusinessSitesReadResponse:
        repository = BusinessProvisioningRepository(database)
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site["public_id"]) for site in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)

        return BusinessSitesReadResponse(
            business=BusinessReference(public_id=str(business["public_id"]), name=str(business["name"])),
            sites=[self._build_site_view(site) for site in sites],
        )

    async def create_business_site(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
        payload: BusinessSiteCreateRequest,
    ) -> BusinessSiteCreateResponse:
        repository = BusinessProvisioningRepository(database)
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site["public_id"]) for site in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)
        self._ensure_business_allows_site_creation(business=business)

        subscription = await repository.get_current_subscription_by_business_id(
            business_public_id=business_public_id,
        )
        current_non_archived_site_count = await repository.count_non_archived_sites_for_business(
            business_public_id=business_public_id,
        )
        site_capacity = self._build_site_capacity_summary(
            business=business,
            subscription=subscription,
            current_non_archived_site_count=current_non_archived_site_count,
        )
        if current_non_archived_site_count >= site_capacity.effective_site_limit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Additional site entitlement required",
            )

        now = datetime.now(UTC)
        site = SiteDocument(
            public_id=new_public_id("site"),
            organisation_id=str(business["organisation_id"]),
            business_id=business_public_id,
            name=payload.name.strip(),
            state="active",
            timezone=(payload.timezone.strip() if payload.timezone else str(business.get("timezone", "Europe/London"))),
            locale=(payload.locale.strip() if payload.locale else str(business.get("locale", "en-GB"))),
            language=(payload.language.strip() if payload.language else str(business.get("language", "en-GB"))),
            created_at=now,
            updated_at=now,
        ).model_dump(mode="json")
        await repository.insert_site(site)

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.site.created",
                entity_type="site",
                entity_public_id=site["public_id"],
                organisation_public_id=str(business["organisation_id"]),
                business_public_id=str(business["public_id"]),
                site_public_id=site["public_id"],
                actor=audit_service.actor_from_context(context),
                metadata={
                    "name": site["name"],
                    "state": site["state"],
                    "remaining_site_capacity": max(0, site_capacity.effective_site_limit - (current_non_archived_site_count + 1)),
                },
                created_at=now,
            ),
        )

        return BusinessSiteCreateResponse(
            business=BusinessReference(public_id=str(business["public_id"]), name=str(business["name"])),
            site=self._build_site_view(site),
            site_capacity=self._build_site_capacity_summary(
                business=business,
                subscription=subscription,
                current_non_archived_site_count=current_non_archived_site_count + 1,
            ),
        )

    async def list_business_memberships(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
    ) -> BusinessMembershipsReadResponse:
        repository = BusinessProvisioningRepository(database)
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site["public_id"] ) for site in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)

        memberships = await repository.list_memberships_applicable_to_business(
            organisation_public_id=str(business["organisation_id"]),
            business_public_id=business_public_id,
            site_public_ids=site_public_ids,
        )

        return BusinessMembershipsReadResponse(
            business=BusinessReference(public_id=str(business["public_id"]), name=str(business["name"])),
            memberships=[self._build_membership_view(membership) for membership in memberships if membership.get("user")],
        )

    async def add_business_membership(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
        payload: BusinessMembershipCreateRequest,
    ) -> BusinessMembershipCreateResponse:
        repository = BusinessProvisioningRepository(database)
        await auth_service.require_fresh_reauthentication(
            database=database,
            context=context,
            action="foundation.membership.manage",
        )
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site["public_id"]) for site in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)
        self._ensure_business_allows_membership_mutation(business=business)

        principal_type = self._principal_type(context)
        if payload.role == "business_owner" and principal_type != "platform_owner":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only platform owner can assign business_owner")

        organisation_public_id = str(business["organisation_id"])
        if payload.role == "business_owner" and payload.scope_type != "business":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="business_owner must be business-scoped")
        if payload.role in {"organisation_admin", "finance_org"} and payload.scope_type != "organisation":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{payload.role} must be organisation-scoped")

        if payload.scope_type == "organisation":
            if payload.scope_public_id and payload.scope_public_id != organisation_public_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organisation scope does not match business organisation")
            resolved_scope_id = organisation_public_id
        elif payload.scope_type == "business":
            if payload.scope_public_id and payload.scope_public_id != business_public_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Business scope does not match target business")
            resolved_scope_id = business_public_id
        else:
            if not payload.scope_public_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Site scope requires scope_public_id")
            site = await repository.get_site_by_public_id(site_public_id=payload.scope_public_id)
            if site is None or str(site.get("business_id", "")) != business_public_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Site does not belong to target business")
            resolved_scope_id = str(site["public_id"])

        existing_user = await repository.get_user_by_email(email=str(payload.email))
        created_user_shell = False
        if existing_user is None:
            if not payload.display_name:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="display_name is required when creating a new tenant user shell")
            existing_user = UserDocument(
                public_id=new_public_id("usr"),
                email=payload.email.lower().strip(),
                principal_type="tenant_user",
                organisation_id=organisation_public_id,
                state="pending_activation",
                display_name=payload.display_name.strip(),
                password_change_required=True,
                mfa_required=True,
            ).model_dump(mode="json")
            await repository.insert_user(existing_user)
            created_user_shell = True
        else:
            if str(existing_user.get("principal_type", "")) != "tenant_user":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Cannot assign tenant memberships to this principal", "invalid_principal_type"))
            if str(existing_user.get("organisation_id", "")) != organisation_public_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("User belongs to a different organisation", "cross_organisation_membership_blocked"))

        existing_membership = await repository.find_active_membership(
            user_public_id=str(existing_user["public_id"]),
            scope_type=payload.scope_type,
            scope_id=resolved_scope_id,
            role=payload.role,
        )
        if existing_membership is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Matching active membership already exists", "membership_already_exists"))

        membership = MembershipDocument(
            public_id=new_public_id("mbr"),
            user_id=str(existing_user["public_id"]),
            organisation_id=organisation_public_id,
            scope_type=payload.scope_type,
            scope_id=resolved_scope_id,
            role=payload.role,
        ).model_dump(mode="json")
        await repository.insert_membership(membership)

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.membership.added",
                entity_type="membership",
                entity_public_id=membership["public_id"],
                organisation_public_id=organisation_public_id,
                business_public_id=business_public_id,
                actor=audit_service.actor_from_context(context),
                target_user_public_id=str(existing_user["public_id"]),
                metadata={
                    "role": membership["role"],
                    "scope_type": membership["scope_type"],
                    "scope_id": membership["scope_id"],
                    "created_user_shell": created_user_shell,
                    "user_email": existing_user["email"],
                },
                created_at=self._coerce_utc(membership["created_at"]),
            ),
        )

        membership_with_user = dict(membership)
        membership_with_user["user"] = existing_user

        return BusinessMembershipCreateResponse(
            business=BusinessReference(public_id=str(business["public_id"]), name=str(business["name"])),
            user=self._user_summary(existing_user),
            membership=self._build_membership_view(membership_with_user),
            created_user_shell=created_user_shell,
        )


    async def archive_business_membership(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
        membership_public_id: str,
    ) -> BusinessMembershipArchiveResponse:
        repository = BusinessProvisioningRepository(database)
        await auth_service.require_fresh_reauthentication(
            database=database,
            context=context,
            action="foundation.membership.manage",
        )
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site["public_id"]) for site in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)
        self._ensure_business_allows_membership_mutation(business=business)

        membership = await repository.get_membership_with_user_by_public_id(membership_public_id=membership_public_id)
        if membership is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
        if membership.get("archived_at") is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Membership is already archived", "membership_already_archived"))

        organisation_public_id = str(business["organisation_id"])
        scope_type = str(membership.get("scope_type", ""))
        scope_id = str(membership.get("scope_id", ""))
        if str(membership.get("organisation_id", "")) != organisation_public_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership is outside target business organisation")
        if scope_type == "business" and scope_id != business_public_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership is outside target business")
        if scope_type == "site" and scope_id not in site_public_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership is outside target business")
        if scope_type == "organisation" and scope_id != organisation_public_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership is outside target business organisation")

        principal_type = self._principal_type(context)
        membership_role = str(membership.get("role", ""))
        if membership_role == "business_owner" and principal_type != "platform_owner":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only platform owner can remove business_owner")

        if membership_role == "business_owner":
            owner_count = await repository.count_active_business_owner_memberships(business_public_id=business_public_id)
            if owner_count <= 1:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Business must retain at least one active business_owner", "last_business_owner_required"))

        archived_at = datetime.now(UTC)
        await repository.archive_membership(
            membership_public_id=membership_public_id,
            archived_at=archived_at,
            updated_at=archived_at,
        )

        refreshed = await repository.get_membership_with_user_by_public_id(membership_public_id=membership_public_id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Archived membership could not be reloaded")

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.membership.archived",
                entity_type="membership",
                entity_public_id=str(refreshed["public_id"]),
                organisation_public_id=organisation_public_id,
                business_public_id=business_public_id,
                actor=audit_service.actor_from_context(context),
                target_user_public_id=(str(refreshed.get("user_id", "")).strip() or None),
                metadata={
                    "role": str(refreshed.get("role", "")),
                    "scope_type": str(refreshed.get("scope_type", "")),
                    "scope_id": str(refreshed.get("scope_id", "")),
                    "archived_at": self._coerce_iso(archived_at),
                },
                created_at=archived_at,
            ),
        )

        return BusinessMembershipArchiveResponse(
            business=BusinessReference(public_id=str(business["public_id"]), name=str(business["name"])),
            membership=self._build_membership_view(refreshed),
        )



    async def update_business_site_capacity(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
        payload: BusinessSiteCapacityUpdateRequest,
    ) -> BusinessSiteCapacityUpdateResponse:
        repository = BusinessProvisioningRepository(database)
        await auth_service.require_fresh_reauthentication(
            database=database,
            context=context,
            action="foundation.business.site_capacity_update",
        )
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        subscription = await repository.get_current_subscription_by_business_id(
            business_public_id=business_public_id,
        )

        updated_at = datetime.now(UTC)
        included_site_limit, _ = self._site_capacity_inputs(business=business, subscription=subscription)
        await repository.update_business_site_capacity(
            business_public_id=business_public_id,
            additional_site_slots=payload.additional_site_slots,
            updated_at=updated_at,
        )
        await repository.update_subscription_site_capacity(
            business_public_id=business_public_id,
            additional_site_slots=payload.additional_site_slots,
            included_site_limit=included_site_limit,
            updated_at=updated_at,
        )
        refreshed = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Business could not be reloaded")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        non_archived_sites = [site for site in sites if str(site.get("state", "")) != "archived"]
        refreshed_subscription = await repository.get_current_subscription_by_business_id(
            business_public_id=business_public_id,
        )
        site_capacity = self._build_site_capacity_summary(
            business=refreshed,
            subscription=refreshed_subscription,
            current_non_archived_site_count=len(non_archived_sites),
        )

        if len(non_archived_sites) > site_capacity.effective_site_limit:
            retained_ids = payload.retained_active_site_public_ids or []
            retained_set = {str(site_id) for site_id in retained_ids}
            valid_site_ids = {str(site["public_id"]) for site in non_archived_sites}

            if len(retained_set) != site_capacity.effective_site_limit:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Must specify exactly {site_capacity.effective_site_limit} retained active site(s)",
                )
            if not retained_set.issubset(valid_site_ids):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Retained active sites must belong to the business and be non-archived",
                )

            for site in non_archived_sites:
                target_state = "active" if str(site["public_id"]) in retained_set else "read_only"
                if str(site.get("state", "")) != target_state:
                    await repository.set_site_state(
                        site_public_id=str(site["public_id"]),
                        state=target_state,
                        updated_at=updated_at,
                    )

        site_capacity_summary = self._build_site_capacity_summary(
            business=refreshed,
            subscription=refreshed_subscription,
            current_non_archived_site_count=len(non_archived_sites),
        )

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.business.site_capacity_updated",
                entity_type="business",
                entity_public_id=str(refreshed["public_id"]),
                organisation_public_id=str(refreshed["organisation_id"]),
                business_public_id=str(refreshed["public_id"]),
                actor=audit_service.actor_from_context(context),
                metadata={
                    "included_site_limit": site_capacity_summary.included_site_limit,
                    "additional_site_slots": site_capacity_summary.additional_site_slots,
                    "effective_site_limit": site_capacity_summary.effective_site_limit,
                    "current_non_archived_site_count": site_capacity_summary.current_non_archived_site_count,
                    "remaining_site_capacity": site_capacity_summary.remaining_site_capacity,
                    "retained_active_site_public_ids": payload.retained_active_site_public_ids or [],
                },
                created_at=updated_at,
            ),
        )

        return BusinessSiteCapacityUpdateResponse(
            business=BusinessReference(public_id=str(refreshed["public_id"]), name=str(refreshed["name"])),
            site_capacity=site_capacity_summary,
        )


    async def activate_business(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
    ) -> BusinessActivateResponse:
        repository = BusinessProvisioningRepository(database)
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site["public_id"]) for site in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)

        business_state = str(business.get("state", ""))
        if business_state == "active":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Business is already active", "business_already_active"))
        if business_state in {"read_only", "suspended", "archived"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Business cannot be activated from state: {business_state}")

        subscription = await repository.get_current_subscription_by_business_id(business_public_id=business_public_id)
        has_active_subscription = bool(subscription) and str(subscription.get("state", "")) == "active"
        has_active_business_owner = (await repository.count_active_business_owner_memberships(business_public_id=business_public_id)) >= 1
        has_active_site = (await repository.count_active_sites_for_business(business_public_id=business_public_id)) >= 1

        checks = BusinessActivationChecks(
            has_active_subscription=has_active_subscription,
            has_active_business_owner=has_active_business_owner,
            has_active_site=has_active_site,
        )

        if not has_active_subscription:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Business requires an active subscription before activation", "active_subscription_required"))
        if not has_active_business_owner:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Business must retain at least one active business_owner before activation", "active_business_owner_required"))
        if not has_active_site:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Business requires at least one active site before activation", "active_site_required"))

        updated_at = datetime.now(UTC)
        await repository.update_business_state(
            business_public_id=business_public_id,
            state="active",
            updated_at=updated_at,
        )
        refreshed = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Activated business could not be reloaded")

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.business.activated",
                entity_type="business",
                entity_public_id=str(refreshed["public_id"]),
                organisation_public_id=str(refreshed["organisation_id"]),
                business_public_id=str(refreshed["public_id"]),
                actor=audit_service.actor_from_context(context),
                metadata={
                    "state": str(refreshed.get("state", "")),
                    "activation_checks": checks.model_dump(mode="json"),
                },
                created_at=updated_at,
            ),
        )

        return BusinessActivateResponse(
            business=self._build_business_view(refreshed),
            activation_checks=checks,
        )


    async def suspend_business_user(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
        user_public_id: str,
    ) -> BusinessUserSuspendResponse:
        repository = BusinessProvisioningRepository(database)
        await auth_service.require_fresh_reauthentication(
            database=database,
            context=context,
            action="foundation.user.suspend",
        )
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site["public_id"]) for site in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)
        self._ensure_business_allows_membership_mutation(business=business)

        user = await repository.get_user_by_public_id(user_public_id=user_public_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if str(user.get("principal_type", "")) == "platform_owner":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot suspend platform owner from tenant business context")
        if str(user.get("organisation_id", "")) != str(business.get("organisation_id", "")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is outside target business organisation")
        if str(user.get("state", "")) == "suspended":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("User is already suspended", "user_already_suspended"))

        applicable_memberships = await repository.list_active_memberships_for_user_applicable_to_business(
            user_public_id=user_public_id,
            organisation_public_id=str(business["organisation_id"]),
            business_public_id=business_public_id,
            site_public_ids=site_public_ids,
        )
        if not applicable_memberships:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is outside target business scope")

        principal_type = self._principal_type(context)
        target_has_business_owner = any(
            str(membership.get("role", "")) == "business_owner" and str(membership.get("scope_type", "")) == "business" and str(membership.get("scope_id", "")) == business_public_id
            for membership in applicable_memberships
        )
        if target_has_business_owner and principal_type != "platform_owner":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only platform owner can suspend business_owner")
        if target_has_business_owner:
            owner_count = await repository.count_active_business_owner_memberships(business_public_id=business_public_id)
            if owner_count <= 1:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("Business must retain at least one active business_owner", "last_business_owner_required"))

        updated_at = datetime.now(UTC)
        previous_state = str(user.get("state", "active"))
        await repository.set_user_state(
            user_public_id=user_public_id,
            state="suspended",
            updated_at=updated_at,
            suspension_restore_state=previous_state,
        )
        revoked_session_count, revoked_refresh_token_count = await repository.revoke_sessions_for_user(
            user_public_id=user_public_id,
            revoked_at=updated_at,
        )
        refreshed_user = await repository.get_user_by_public_id(user_public_id=user_public_id)
        if refreshed_user is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Suspended user could not be reloaded")

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.user.suspended",
                entity_type="user",
                entity_public_id=str(refreshed_user["public_id"]),
                organisation_public_id=str(business["organisation_id"]),
                business_public_id=str(business["public_id"]),
                actor=audit_service.actor_from_context(context),
                target_user_public_id=str(refreshed_user["public_id"]),
                metadata={
                    "previous_state": previous_state,
                    "new_state": str(refreshed_user.get("state", "")),
                    "revoked_session_count": revoked_session_count,
                    "revoked_refresh_token_count": revoked_refresh_token_count,
                },
                created_at=updated_at,
            ),
        )

        return BusinessUserSuspendResponse(
            business=BusinessReference(public_id=str(business["public_id"]), name=str(business["name"])),
            user=self._user_summary(refreshed_user),
            revoked_session_count=revoked_session_count,
            revoked_refresh_token_count=revoked_refresh_token_count,
        )

    async def reactivate_business_user(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
        user_public_id: str,
    ) -> BusinessUserReactivateResponse:
        repository = BusinessProvisioningRepository(database)
        await auth_service.require_fresh_reauthentication(
            database=database,
            context=context,
            action="foundation.user.reactivate",
        )
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site["public_id"]) for site in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)
        self._ensure_business_allows_membership_mutation(business=business)

        user = await repository.get_user_by_public_id(user_public_id=user_public_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if str(user.get("principal_type", "")) == "platform_owner":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot reactivate platform owner from tenant business context")
        if str(user.get("organisation_id", "")) != str(business.get("organisation_id", "")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is outside target business organisation")
        if str(user.get("state", "")) != "suspended":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_conflict_detail("User is not suspended", "user_not_suspended"))

        applicable_memberships = await repository.list_active_memberships_for_user_applicable_to_business(
            user_public_id=user_public_id,
            organisation_public_id=str(business["organisation_id"]),
            business_public_id=business_public_id,
            site_public_ids=site_public_ids,
        )
        if not applicable_memberships:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is outside target business scope")

        target_has_business_owner = any(
            str(membership.get("role", "")) == "business_owner" and str(membership.get("scope_type", "")) == "business" and str(membership.get("scope_id", "")) == business_public_id
            for membership in applicable_memberships
        )
        if target_has_business_owner and self._principal_type(context) != "platform_owner":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only platform owner can reactivate business_owner")

        restored_state = str(user.get("suspension_restore_state") or "active")
        updated_at = datetime.now(UTC)
        await repository.set_user_state(
            user_public_id=user_public_id,
            state=restored_state,
            updated_at=updated_at,
            suspension_restore_state=None,
        )
        refreshed_user = await repository.get_user_by_public_id(user_public_id=user_public_id)
        if refreshed_user is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Reactivated user could not be reloaded")

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.user.reactivated",
                entity_type="user",
                entity_public_id=str(refreshed_user["public_id"]),
                organisation_public_id=str(business["organisation_id"]),
                business_public_id=str(business["public_id"]),
                actor=audit_service.actor_from_context(context),
                target_user_public_id=str(refreshed_user["public_id"]),
                metadata={
                    "restored_state": restored_state,
                    "new_state": str(refreshed_user.get("state", "")),
                },
                created_at=updated_at,
            ),
        )

        return BusinessUserReactivateResponse(
            business=BusinessReference(public_id=str(business["public_id"]), name=str(business["name"])),
            user=self._user_summary(refreshed_user),
        )


business_provisioning_service = BusinessProvisioningService()
