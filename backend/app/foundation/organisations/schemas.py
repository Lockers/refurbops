from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OrganisationView(BaseModel):
    public_id: str
    name: str
    state: str
    created_at: str
    updated_at: str


class OrganisationReadResponse(BaseModel):
    status: Literal["organisation_loaded"] = "organisation_loaded"
    organisation: OrganisationView


class OrganisationUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class OrganisationUpdateResponse(BaseModel):
    status: Literal["organisation_updated"] = "organisation_updated"
    organisation: OrganisationView
