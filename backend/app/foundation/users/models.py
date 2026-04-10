from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


UserState = Literal["pending_activation", "active", "suspended", "deactivated"]
PrincipalType = Literal["tenant_user", "platform_owner", "system_support"]


class UserDocument(BaseModel):
    public_id: str
    email: EmailStr
    principal_type: PrincipalType
    organisation_id: str | None = None
    state: UserState = "active"
    display_name: str | None = None
    password_change_required: bool = False
    mfa_required: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
