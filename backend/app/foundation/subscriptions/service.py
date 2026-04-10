from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.auth.schemas import AuthenticatedRequestContext
from app.auth.service import auth_service
from app.audit.schemas import AuditEventCreate
from app.audit.service import audit_service
from app.foundation.subscriptions.repository import SubscriptionRepository
from app.foundation.subscriptions.schemas import (
    BusinessReference,
    BusinessSubscriptionHistoryResponse,
    BusinessSubscriptionReadResponse,
    BusinessSubscriptionUpsertRequest,
    BusinessSubscriptionUpsertResponse,
    BusinessSubscriptionView,
    SiteCapacityMirrorView,
    SubscriptionEntitlementsView,
    SubscriptionHistoryEntryView,
)
from app.shared.utils.public_ids import new_public_id


class SubscriptionService:
    @staticmethod
    def _derive_business_state_from_subscription(*, current_business_state: str, subscription_state: str) -> str:
        if subscription_state in {"past_due", "read_only", "cancelled"}:
            return "read_only"
        if subscription_state == "active" and current_business_state == "read_only":
            return "active"
        return current_business_state

    def _ensure_business_scope(
        self,
        *,
        context: AuthenticatedRequestContext,
        business_document: dict[str, Any],
    ) -> None:
        principal_type = str(context.user.get("principal_type", "")).strip()
        if principal_type == "platform_owner":
            return

        business_public_id = str(business_document["public_id"])
        organisation_public_id = str(business_document["organisation_id"])
        for membership in context.memberships:
            scope_type = str(membership.get("scope_type", "")).strip()
            scope_id = str(membership.get("scope_id", "")).strip()
            if scope_type == "business" and scope_id == business_public_id:
                return
            if scope_type == "organisation" and scope_id == organisation_public_id:
                return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business is outside authorized scope",
        )

    @staticmethod
    def _to_iso(value: Any) -> str:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.isoformat()
        return str(value)

    def _build_entitlements_view(self, entitlements: dict[str, Any]) -> SubscriptionEntitlementsView:
        return SubscriptionEntitlementsView(
            backmarket_enabled=bool(entitlements.get("backmarket_enabled", True)),
            pricer_enabled=bool(entitlements.get("pricer_enabled", False)),
            kpi_intelligence_enabled=bool(entitlements.get("kpi_intelligence_enabled", False)),
            parts_intelligence_enabled=bool(entitlements.get("parts_intelligence_enabled", False)),
            included_site_limit=int(entitlements.get("included_site_limit", 1)),
            additional_site_slots=int(entitlements.get("additional_site_slots", 0)),
        )

    def _build_subscription_view(self, document: dict[str, Any]) -> BusinessSubscriptionView:
        entitlements = dict(document.get("entitlements", {}))
        return BusinessSubscriptionView(
            public_id=str(document["public_id"]),
            organisation_id=str(document["organisation_id"]),
            business_id=str(document["business_id"]),
            state=str(document["state"]),
            plan_code=str(document["plan_code"]),
            billing_currency=str(document["billing_currency"]),
            billing_cadence=str(document["billing_cadence"]),
            entitlements=self._build_entitlements_view(entitlements),
            created_at=self._to_iso(document.get("created_at")),
            updated_at=self._to_iso(document.get("updated_at")),
        )

    def _build_subscription_history_view(self, document: dict[str, Any]) -> SubscriptionHistoryEntryView:
        entitlements = dict(document.get("entitlements", {}))
        return SubscriptionHistoryEntryView(
            public_id=str(document["public_id"]),
            subscription_public_id=str(document["subscription_public_id"]),
            organisation_id=str(document["organisation_id"]),
            business_id=str(document["business_id"]),
            state=str(document["state"]),
            plan_code=str(document["plan_code"]),
            billing_currency=str(document["billing_currency"]),
            billing_cadence=str(document["billing_cadence"]),
            entitlements=self._build_entitlements_view(entitlements),
            change_type=str(document["change_type"]),
            recorded_at=self._to_iso(document.get("recorded_at")),
        )

    @staticmethod
    def _build_business_reference(document: dict[str, Any]) -> BusinessReference:
        return BusinessReference(
            public_id=str(document["public_id"]),
            name=str(document["name"]),
        )

    @staticmethod
    def _build_site_capacity_view(*, included_site_limit: int, additional_site_slots: int) -> SiteCapacityMirrorView:
        return SiteCapacityMirrorView(
            included_site_limit=included_site_limit,
            additional_site_slots=additional_site_slots,
            effective_site_limit=included_site_limit + additional_site_slots,
        )

    async def get_business_subscription(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
    ) -> BusinessSubscriptionReadResponse:
        repository = SubscriptionRepository(database)
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        self._ensure_business_scope(context=context, business_document=business)

        subscription = await repository.get_current_subscription_by_business_id(business_public_id=business_public_id)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current subscription not configured")

        return BusinessSubscriptionReadResponse(
            business=self._build_business_reference(business),
            subscription=self._build_subscription_view(subscription),
            site_capacity=self._build_site_capacity_view(
                included_site_limit=int(subscription["entitlements"].get("included_site_limit", 1)),
                additional_site_slots=int(subscription["entitlements"].get("additional_site_slots", 0)),
            ),
        )

    async def get_business_subscription_history(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
    ) -> BusinessSubscriptionHistoryResponse:
        repository = SubscriptionRepository(database)
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        self._ensure_business_scope(context=context, business_document=business)
        history_documents = await repository.list_subscription_history_by_business_id(business_public_id=business_public_id)
        return BusinessSubscriptionHistoryResponse(
            business=self._build_business_reference(business),
            history=[self._build_subscription_history_view(document) for document in history_documents],
        )

    async def upsert_business_subscription(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
        payload: BusinessSubscriptionUpsertRequest,
    ) -> BusinessSubscriptionUpsertResponse:
        repository = SubscriptionRepository(database)
        await auth_service.require_fresh_reauthentication(
            database=database,
            context=context,
            action="foundation.subscription.manage",
        )
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        now = datetime.now(UTC)
        entitlements = {
            "backmarket_enabled": payload.backmarket_enabled,
            "pricer_enabled": payload.pricer_enabled,
            "kpi_intelligence_enabled": payload.kpi_intelligence_enabled,
            "parts_intelligence_enabled": payload.parts_intelligence_enabled,
            "included_site_limit": payload.included_site_limit,
            "additional_site_slots": payload.additional_site_slots,
        }

        existing_current = await repository.get_current_subscription_by_business_id(business_public_id=business_public_id)
        change_type = "created" if existing_current is None else "updated"

        subscription = await repository.upsert_current_subscription(
            business_public_id=business_public_id,
            organisation_public_id=str(business["organisation_id"]),
            subscription_public_id=new_public_id("sub"),
            state=payload.state,
            plan_code=payload.plan_code,
            billing_currency=payload.billing_currency.upper(),
            billing_cadence=payload.billing_cadence,
            entitlements=entitlements,
            created_at=now,
            updated_at=now,
        )

        await repository.append_subscription_history(
            public_id=new_public_id("subh"),
            subscription_public_id=str(subscription["public_id"]),
            organisation_id=str(subscription["organisation_id"]),
            business_id=str(subscription["business_id"]),
            state=str(subscription["state"]),
            plan_code=str(subscription["plan_code"]),
            billing_currency=str(subscription["billing_currency"]),
            billing_cadence=str(subscription["billing_cadence"]),
            entitlements=dict(subscription.get("entitlements", {})),
            change_type=change_type,
            recorded_at=now,
        )

        await repository.mirror_site_capacity_to_business(
            business_public_id=business_public_id,
            included_site_limit=payload.included_site_limit,
            additional_site_slots=payload.additional_site_slots,
            updated_at=now,
        )

        derived_business_state = self._derive_business_state_from_subscription(
            current_business_state=str(business.get("state", "")),
            subscription_state=payload.state,
        )
        if derived_business_state != str(business.get("state", "")):
            await repository.update_business_state(
                business_public_id=business_public_id,
                state=derived_business_state,
                updated_at=now,
            )

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type=f"foundation.subscription.{change_type}",
                entity_type="subscription",
                entity_public_id=str(subscription["public_id"]),
                organisation_public_id=str(subscription["organisation_id"]),
                business_public_id=str(subscription["business_id"]),
                actor=audit_service.actor_from_context(context),
                metadata={
                    "state": str(subscription["state"]),
                    "plan_code": str(subscription["plan_code"]),
                    "billing_currency": str(subscription["billing_currency"]),
                    "billing_cadence": str(subscription["billing_cadence"]),
                    "entitlements": dict(subscription.get("entitlements", {})),
                    "site_capacity": {
                        "included_site_limit": payload.included_site_limit,
                        "additional_site_slots": payload.additional_site_slots,
                        "effective_site_limit": payload.included_site_limit + payload.additional_site_slots,
                    },
                    "derived_business_state": derived_business_state,
                },
                created_at=now,
            ),
        )

        return BusinessSubscriptionUpsertResponse(
            business=self._build_business_reference(business),
            subscription=self._build_subscription_view(subscription),
            site_capacity=self._build_site_capacity_view(
                included_site_limit=payload.included_site_limit,
                additional_site_slots=payload.additional_site_slots,
            ),
        )


subscription_service = SubscriptionService()
