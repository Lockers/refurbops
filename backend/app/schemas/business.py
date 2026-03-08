from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BackMarketIntegrationConfig(BaseModel):
    """
    Business-scoped Back Market integration settings.

    These values belong to the business, not global application config,
    because RefurbOps is multi-business from day one.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = False
    api_key: str | None = None
    accept_language: str | None = None
    company_name: str | None = None
    integration_name: str | None = None
    contact_email: EmailStr | None = None
    proxy_url: str | None = None


class BusinessIntegrations(BaseModel):
    """
    Container for business integration settings.

    Keep this small for now. More providers can be added later without
    restructuring the business document shape.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    backmarket: BackMarketIntegrationConfig | None = None


class BusinessDocument(BaseModel):
    """
    Minimal business document schema required for Module 01.

    This intentionally includes only the fields needed for inbound sync
    plus the existing VAT/business metadata already defined in the docs.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str | None = Field(default=None, alias="_id")
    name: str

    vat_registered: bool | None = None
    vat_scheme: str | None = None
    vat_period: str | None = None
    vat_period_start: datetime | None = None

    integrations: BusinessIntegrations = Field(default_factory=BusinessIntegrations)

    created_at: datetime | None = None
    updated_at: datetime | None = None


class BusinessBackMarketConfigResult(BaseModel):
    """
    Narrow response/helper model used by repository/service layers when they
    only need Back Market settings for a specific business.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    business_id: str
    business_name: str
    config: BackMarketIntegrationConfig


class BusinessSeedPayload(BaseModel):
    """
    Optional helper schema for local/manual seed tooling later.

    Not required by the current API layer, but useful for scripts or one-off
    local setup without redefining the document shape elsewhere.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str = Field(alias="_id")
    name: str

    vat_registered: bool | None = None
    vat_scheme: str | None = None
    vat_period: str | None = None
    vat_period_start: datetime | None = None

    integrations: BusinessIntegrations = Field(default_factory=BusinessIntegrations)

    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_mongo(self) -> dict[str, Any]:
        """
        Return a Mongo-friendly dict using aliases.

        This is helpful for seed scripts where `_id` must be emitted exactly
        as stored in MongoDB.
        """
        return self.model_dump(by_alias=True, exclude_none=True)
