from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


OrganisationState = Literal["active", "suspended", "archived"]


class OrganisationDocument(BaseModel):
    public_id: str
    name: str
    state: OrganisationState = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
