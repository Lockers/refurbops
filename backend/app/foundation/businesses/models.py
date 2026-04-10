from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


BusinessState = Literal["pending_setup", "active", "read_only", "suspended", "archived"]


class BusinessDocument(BaseModel):
    public_id: str
    organisation_id: str
    name: str
    state: BusinessState = "pending_setup"
    timezone: str = "Europe/London"
    country_code: str = "GB"
    currency_code: str = "GBP"
    locale: str = "en-GB"
    language: str = "en-GB"
    included_site_limit: int = 1
    additional_site_slots: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
