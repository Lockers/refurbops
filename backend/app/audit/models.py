from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogDocument(BaseModel):
    public_id: str
    event_type: str
    entity_type: str
    entity_public_id: str
    organisation_id: str | None = None
    business_id: str | None = None
    site_id: str | None = None
    actor_user_id: str | None = None
    actor_principal_type: str | None = None
    actor_email: str | None = None
    actor_session_id: str | None = None
    target_user_id: str | None = None
    reason_code: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
