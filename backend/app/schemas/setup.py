from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.business import BackMarketIntegrationConfig


class SetupBusinessPayload(BaseModel):
    """
    Business payload used during first-time bootstrap.

    This is intentionally minimal and focused on the fields required to make
    RefurbOps usable for Module 01.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str = Field(alias="_id")
    name: str

    vat_registered: bool = True
    vat_scheme: str | None = None
    vat_period: str | None = None
    vat_period_start: datetime | None = None

    backmarket: BackMarketIntegrationConfig


class SetupUserPayload(BaseModel):
    """
    First user payload used during bootstrap.

    Auth is not implemented yet, so this only stores the initial user record.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str = Field(alias="_id")
    name: str
    email: EmailStr
    role: str = "business_admin"


class SetupBootstrapRequest(BaseModel):
    """
    Request body for the first-time setup/bootstrap endpoint.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    business: SetupBusinessPayload
    user: SetupUserPayload


class SetupBootstrapResponse(BaseModel):
    """
    Response returned after a successful bootstrap.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    business_id: str
    user_id: str
    created: bool = True


class SetupStatusResponse(BaseModel):
    """
    Response indicating whether the system has already been configured.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    is_configured: bool
