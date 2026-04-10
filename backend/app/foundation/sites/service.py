from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.audit.schemas import AuditEventCreate
from app.audit.service import audit_service
from app.auth.schemas import AuthenticatedRequestContext
from app.foundation.sites.repository import SiteRepository
from app.foundation.sites.schemas import SiteReadResponse, SiteUpdateRequest, SiteUpdateResponse, SiteView


class SiteService:
    @staticmethod
    def _coerce_iso(value: Any) -> str:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.isoformat()
        return str(value)

    def _build_view(self, document: dict[str, Any]) -> SiteView:
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
    def _ensure_business_access(
        *,
        context: AuthenticatedRequestContext,
        business: dict[str, Any],
        site_public_ids: list[str],
    ) -> None:
        principal_type = str(context.user.get("principal_type", "")).strip()
        if principal_type == "platform_owner":
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

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Site is outside your allowed scope")

    async def get_site(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        site_public_id: str,
    ) -> SiteReadResponse:
        repository = SiteRepository(database)
        site = await repository.get_site_by_public_id(site_public_id=site_public_id)
        if site is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

        business = await repository.get_business_by_public_id(business_public_id=str(site["business_id"]))
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=str(site["business_id"]))
        site_public_ids = [str(document["public_id"]) for document in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)

        return SiteReadResponse(site=self._build_view(site))

    async def update_site(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        site_public_id: str,
        payload: SiteUpdateRequest,
    ) -> SiteUpdateResponse:
        repository = SiteRepository(database)
        site = await repository.get_site_by_public_id(site_public_id=site_public_id)
        if site is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

        business = await repository.get_business_by_public_id(business_public_id=str(site["business_id"]))
        if business is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

        sites = await repository.list_sites_for_business(business_public_id=str(site["business_id"]))
        site_public_ids = [str(document["public_id"]) for document in sites]
        self._ensure_business_access(context=context, business=business, site_public_ids=site_public_ids)

        if str(site.get("state", "")) == "archived":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot update an archived site")

        payload_data = payload.model_dump(exclude_unset=True)
        if not payload_data:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one field must be provided")

        updates: dict[str, Any] = {}
        changes: dict[str, dict[str, str]] = {}
        for field_name, raw_value in payload_data.items():
            if raw_value is None:
                continue
            new_value = raw_value.strip() if isinstance(raw_value, str) else raw_value
            old_value = site.get(field_name)
            if old_value == new_value:
                continue
            updates[field_name] = new_value
            changes[field_name] = {
                "before": "" if old_value is None else str(old_value),
                "after": "" if new_value is None else str(new_value),
            }

        if not updates:
            return SiteUpdateResponse(site=self._build_view(site))

        updated_at = datetime.now(UTC)
        updates["updated_at"] = updated_at
        await repository.update_site_fields(site_public_id=site_public_id, update_fields=updates)

        refreshed = await repository.get_site_by_public_id(site_public_id=site_public_id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.site.updated",
                entity_type="site",
                entity_public_id=str(refreshed["public_id"]),
                organisation_public_id=str(refreshed["organisation_id"]),
                business_public_id=str(refreshed["business_id"]),
                site_public_id=str(refreshed["public_id"]),
                actor=audit_service.actor_from_context(context),
                metadata={
                    "updated_fields": sorted(changes.keys()),
                    "changes": changes,
                },
                created_at=updated_at,
            ),
        )

        return SiteUpdateResponse(site=self._build_view(refreshed))


site_service = SiteService()
