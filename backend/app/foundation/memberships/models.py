from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


MembershipScopeType = Literal["organisation", "business", "site"]
MembershipRole = Literal[
    "organisation_admin",
    "business_owner",
    "business_admin",
    "backmarket_admin",
    "manager",
    "finance",
    "finance_org",
    "viewer",
    "technician",
]


class MembershipDocument(BaseModel):
    public_id: str
    user_id: str
    organisation_id: str
    scope_type: MembershipScopeType
    scope_id: str
    role: MembershipRole
    archived_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
