from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


SiteState = Literal["active", "read_only", "archived"]


class SiteDocument(BaseModel):
    public_id: str
    organisation_id: str
    business_id: str
    name: str
    state: SiteState = "active"
    timezone: str | None = None
    locale: str | None = None
    language: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
