from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AuditActorContext(BaseModel):
    user_public_id: str | None = None
    principal_type: str | None = None
    email: str | None = None
    session_public_id: str | None = None


class AuditEventCreate(BaseModel):
    event_type: str
    entity_type: str
    entity_public_id: str
    organisation_public_id: str | None = None
    business_public_id: str | None = None
    site_public_id: str | None = None
    actor: AuditActorContext = Field(default_factory=AuditActorContext)
    target_user_public_id: str | None = None
    reason_code: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditActorView(BaseModel):
    user_public_id: str | None = None
    principal_type: str | None = None
    email: str | None = None


class AuditEventView(BaseModel):
    public_id: str
    event_type: str
    entity_type: str
    entity_public_id: str
    organisation_id: str | None = None
    business_id: str | None = None
    site_id: str | None = None
    actor: AuditActorView
    target_user_id: str | None = None
    reason_code: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class AuditEventsPageView(BaseModel):
    returned_count: int
    next_before: str | None = None


class BusinessAuditEventsReadResponse(BaseModel):
    status: Literal["audit_events_loaded"] = "audit_events_loaded"
    business_public_id: str
    events: list[AuditEventView]
    page: AuditEventsPageView
