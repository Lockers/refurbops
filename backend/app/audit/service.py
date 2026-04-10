from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.api.errors import not_found, unprocessable
from app.api.middleware.request_context import get_correlation_id
from app.audit.models import AuditLogDocument
from app.audit.repository import AuditRepository
from app.audit.schemas import (
    AuditActorContext,
    AuditActorView,
    AuditEventCreate,
    AuditEventsPageView,
    AuditEventView,
    BusinessAuditEventsReadResponse,
)
from app.auth.schemas import AuthenticatedRequestContext
from app.shared.utils.public_ids import new_public_id


class AuditService:
    @staticmethod
    def actor_from_context(context: AuthenticatedRequestContext) -> AuditActorContext:
        user = context.user
        session = context.session
        return AuditActorContext(
            user_public_id=str(user.get('public_id', '')).strip() or None,
            principal_type=str(user.get('principal_type', '')).strip() or None,
            email=str(user.get('email', '')).strip() or None,
            session_public_id=str(session.get('public_id', '')).strip() or None,
        )

    @staticmethod
    def actor_from_user(user: dict[str, Any], *, session_public_id: str | None = None) -> AuditActorContext:
        return AuditActorContext(
            user_public_id=str(user.get('public_id', '')).strip() or None,
            principal_type=str(user.get('principal_type', '')).strip() or None,
            email=str(user.get('email', '')).strip() or None,
            session_public_id=(session_public_id.strip() if session_public_id else None),
        )

    @staticmethod
    def system_actor() -> AuditActorContext:
        return AuditActorContext(principal_type='system')

    async def record_event(self, *, database: AsyncDatabase, event: AuditEventCreate) -> None:
        repository = AuditRepository(database)
        document = AuditLogDocument(
            public_id=new_public_id('aud'),
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_public_id=event.entity_public_id,
            organisation_id=event.organisation_public_id,
            business_id=event.business_public_id,
            site_id=event.site_public_id,
            actor_user_id=event.actor.user_public_id,
            actor_principal_type=event.actor.principal_type,
            actor_email=event.actor.email,
            actor_session_id=event.actor.session_public_id,
            target_user_id=event.target_user_public_id,
            reason_code=event.reason_code,
            correlation_id=event.correlation_id or get_correlation_id(),
            metadata=dict(event.metadata),
            created_at=self._coerce_utc(event.created_at),
        ).model_dump(mode='json')
        await repository.insert_audit_log(document=document)

    async def list_business_events(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        business_public_id: str,
        limit: int,
        event_types: list[str] | None = None,
        before: str | None = None,
    ) -> BusinessAuditEventsReadResponse:
        repository = AuditRepository(database)
        business = await repository.get_business_by_public_id(business_public_id=business_public_id)
        if business is None:
            raise not_found("Business not found", reason_code="business_not_found")

        sites = await repository.list_sites_for_business(business_public_id=business_public_id)
        site_public_ids = [str(site.get("public_id", "")).strip() for site in sites if str(site.get("public_id", "")).strip()]
        self._ensure_business_audit_access(context=context, business=business, site_public_ids=site_public_ids)

        before_dt: datetime | None = None
        if before:
            try:
                before_dt = self._parse_before(before)
            except ValueError as exc:
                raise unprocessable("Invalid before cursor", reason_code="invalid_before_cursor") from exc

        events = await repository.list_business_events(
            business_public_id=business_public_id,
            limit=limit,
            event_types=[value for value in (event_types or []) if value],
            before=before_dt,
        )
        event_views = [self._build_event_view(event) for event in events]
        next_before = event_views[-1].created_at if event_views else None
        return BusinessAuditEventsReadResponse(
            business_public_id=business_public_id,
            events=event_views,
            page=AuditEventsPageView(returned_count=len(event_views), next_before=next_before),
        )

    @staticmethod
    def _parse_before(value: str) -> datetime:
        normalized = value.strip()
        if normalized.endswith('Z'):
            normalized = normalized[:-1] + '+00:00'
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _ensure_business_audit_access(
        *,
        context: AuthenticatedRequestContext,
        business: dict[str, Any],
        site_public_ids: list[str],
    ) -> None:
        principal_type = str(context.user.get("principal_type", "")).strip()
        if principal_type == "platform_owner":
            return

        business_public_id = str(business.get("public_id", "")).strip()
        organisation_public_id = str(business.get("organisation_id", "")).strip()
        for membership in context.memberships:
            if str(membership.get("organisation_id", "")).strip() != organisation_public_id:
                continue
            scope_type = str(membership.get("scope_type", "")).strip()
            scope_id = str(membership.get("scope_id", "")).strip()
            if scope_type == "organisation" and scope_id == organisation_public_id:
                return
            if scope_type == "business" and scope_id == business_public_id:
                return
            if scope_type == "site" and scope_id in site_public_ids:
                return

        raise not_found("Business not found", reason_code="business_not_found")

    def _build_event_view(self, document: dict[str, Any]) -> AuditEventView:
        created_at = document.get("created_at")
        return AuditEventView(
            public_id=str(document.get("public_id", "")),
            event_type=str(document.get("event_type", "")),
            entity_type=str(document.get("entity_type", "")),
            entity_public_id=str(document.get("entity_public_id", "")),
            organisation_id=self._clean_optional(document.get("organisation_id")),
            business_id=self._clean_optional(document.get("business_id")),
            site_id=self._clean_optional(document.get("site_id")),
            actor=AuditActorView(
                user_public_id=self._clean_optional(document.get("actor_user_id")),
                principal_type=self._clean_optional(document.get("actor_principal_type")),
                email=self._clean_optional(document.get("actor_email")),
            ),
            target_user_id=self._clean_optional(document.get("target_user_id")),
            reason_code=self._clean_optional(document.get("reason_code")),
            correlation_id=self._clean_optional(document.get("correlation_id")),
            metadata=self._normalize_metadata(document.get("metadata") or {}),
            created_at=self._coerce_iso(created_at),
        )

    @staticmethod
    def _clean_optional(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _normalize_metadata(value: Any) -> Any:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.isoformat()
        if isinstance(value, dict):
            return {str(key): AuditService._normalize_metadata(item) for key, item in value.items()}
        if isinstance(value, list):
            return [AuditService._normalize_metadata(item) for item in value]
        return value

    @staticmethod
    def _coerce_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _coerce_iso(value: Any) -> str:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.isoformat()
        return str(value)


audit_service = AuditService()
