from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SiteView(BaseModel):
    public_id: str
    organisation_id: str
    business_id: str
    name: str
    state: str
    timezone: str | None
    locale: str | None
    language: str | None
    created_at: str
    updated_at: str


class SiteReadResponse(BaseModel):
    status: Literal["site_loaded"] = "site_loaded"
    site: SiteView


class SiteUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
    locale: str | None = Field(default=None, min_length=1, max_length=50)
    language: str | None = Field(default=None, min_length=1, max_length=50)


class SiteUpdateResponse(BaseModel):
    status: Literal["site_updated"] = "site_updated"
    site: SiteView
