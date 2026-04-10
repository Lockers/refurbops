from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.audit.schemas import AuditEventCreate
from app.audit.service import audit_service
from app.auth.schemas import AuthenticatedRequestContext
from app.foundation.organisations.repository import OrganisationRepository
from app.foundation.organisations.schemas import (
    OrganisationReadResponse,
    OrganisationUpdateRequest,
    OrganisationUpdateResponse,
    OrganisationView,
)


class OrganisationService:
    @staticmethod
    def _coerce_iso(value: Any) -> str:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.isoformat()
        return str(value)

    def _build_view(self, document: dict[str, Any]) -> OrganisationView:
        return OrganisationView(
            public_id=str(document["public_id"]),
            name=str(document["name"]),
            state=str(document["state"]),
            created_at=self._coerce_iso(document["created_at"]),
            updated_at=self._coerce_iso(document["updated_at"]),
        )

    @staticmethod
    def _ensure_access(*, context: AuthenticatedRequestContext, organisation_public_id: str) -> None:
        principal_type = str(context.user.get("principal_type", "")).strip()
        if principal_type == "platform_owner":
            return

        for membership in context.memberships:
            if str(membership.get("organisation_id", "")) == organisation_public_id:
                return

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organisation is outside your allowed scope")

    async def get_organisation(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        organisation_public_id: str,
    ) -> OrganisationReadResponse:
        repository = OrganisationRepository(database)
        organisation = await repository.get_by_public_id(organisation_public_id=organisation_public_id)
        if organisation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found")

        self._ensure_access(context=context, organisation_public_id=organisation_public_id)
        return OrganisationReadResponse(organisation=self._build_view(organisation))

    async def update_organisation(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        organisation_public_id: str,
        payload: OrganisationUpdateRequest,
    ) -> OrganisationUpdateResponse:
        repository = OrganisationRepository(database)
        organisation = await repository.get_by_public_id(organisation_public_id=organisation_public_id)
        if organisation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found")

        self._ensure_access(context=context, organisation_public_id=organisation_public_id)
        if str(organisation.get("state", "")) == "archived":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot update an archived organisation")

        name = payload.name.strip()
        if str(organisation.get("name", "")) == name:
            return OrganisationUpdateResponse(organisation=self._build_view(organisation))

        updated_at = datetime.now(UTC)
        changes = {
            "name": {
                "before": str(organisation.get("name", "")),
                "after": name,
            }
        }
        await repository.update_fields(
            organisation_public_id=organisation_public_id,
            update_fields={
                "name": name,
                "updated_at": updated_at,
            },
        )

        refreshed = await repository.get_by_public_id(organisation_public_id=organisation_public_id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found")

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="foundation.organisation.updated",
                entity_type="organisation",
                entity_public_id=str(refreshed["public_id"]),
                organisation_public_id=str(refreshed["public_id"]),
                actor=audit_service.actor_from_context(context),
                metadata={
                    "updated_fields": ["name"],
                    "changes": changes,
                },
                created_at=updated_at,
            ),
        )

        return OrganisationUpdateResponse(organisation=self._build_view(refreshed))


organisation_service = OrganisationService()
