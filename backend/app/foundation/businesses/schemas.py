from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class ProvisionInitialBusinessRequest(BaseModel):
    organisation_name: str = Field(min_length=1, max_length=200)
    business_name: str = Field(min_length=1, max_length=200)
    primary_site_name: str = Field(min_length=1, max_length=200)
    business_owner_email: EmailStr
    business_owner_display_name: str = Field(min_length=1, max_length=200)


class CreatedEntityReference(BaseModel):
    public_id: str
    name: str


class ProvisionedBusinessOwnerUser(BaseModel):
    public_id: str
    email: EmailStr
    display_name: str
    state: str
    principal_type: str


class ProvisionedMembershipReference(BaseModel):
    public_id: str
    role: str
    scope_type: str
    scope_id: str


class ProvisionInitialBusinessResponse(BaseModel):
    status: str = "business_shell_provisioned"
    organisation: CreatedEntityReference
    business: CreatedEntityReference
    primary_site: CreatedEntityReference
    business_owner_user: ProvisionedBusinessOwnerUser
    business_owner_membership: ProvisionedMembershipReference


class BusinessView(BaseModel):
    public_id: str
    organisation_id: str
    name: str
    state: str
    timezone: str
    country_code: str
    currency_code: str
    locale: str
    language: str
    created_at: str
    updated_at: str


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


class BusinessUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    locale: str | None = Field(default=None, min_length=2, max_length=50)
    language: str | None = Field(default=None, min_length=2, max_length=50)


class BusinessUpdateResponse(BaseModel):
    status: Literal["business_updated"] = "business_updated"
    business: BusinessView



class BusinessReadResponse(BaseModel):
    status: Literal["business_loaded"] = "business_loaded"
    business: BusinessView


class BusinessReference(BaseModel):
    public_id: str
    name: str


class BusinessSitesReadResponse(BaseModel):
    status: Literal["business_sites_loaded"] = "business_sites_loaded"
    business: BusinessReference
    sites: list[SiteView]


class MembershipUserSummary(BaseModel):
    public_id: str
    email: EmailStr
    display_name: str | None
    state: str
    principal_type: str


class MembershipView(BaseModel):
    public_id: str
    role: str
    scope_type: str
    scope_id: str
    user: MembershipUserSummary
    archived_at: str | None
    created_at: str
    updated_at: str


class BusinessMembershipsReadResponse(BaseModel):
    status: Literal["business_memberships_loaded"] = "business_memberships_loaded"
    business: BusinessReference
    memberships: list[MembershipView]


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


class BusinessMembershipCreateRequest(BaseModel):
    email: EmailStr
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    role: MembershipRole
    scope_type: MembershipScopeType = "business"
    scope_public_id: str | None = Field(default=None, min_length=1)


class BusinessMembershipCreateResponse(BaseModel):
    status: Literal["membership_added"] = "membership_added"
    business: BusinessReference
    user: MembershipUserSummary
    membership: MembershipView
    created_user_shell: bool


class BusinessMembershipArchiveResponse(BaseModel):
    status: Literal["membership_archived"] = "membership_archived"
    business: BusinessReference
    membership: MembershipView


class BusinessSiteCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
    locale: str | None = Field(default=None, min_length=1, max_length=50)
    language: str | None = Field(default=None, min_length=1, max_length=50)


class SiteCapacitySummary(BaseModel):
    included_site_limit: int
    additional_site_slots: int
    effective_site_limit: int
    current_non_archived_site_count: int
    remaining_site_capacity: int


class BusinessSiteCreateResponse(BaseModel):
    status: Literal["site_created"] = "site_created"
    business: BusinessReference
    site: SiteView
    site_capacity: SiteCapacitySummary


class BusinessSiteCapacityUpdateRequest(BaseModel):
    additional_site_slots: int = Field(ge=0, le=1000)
    retained_active_site_public_ids: list[str] | None = None


class BusinessSiteCapacityUpdateResponse(BaseModel):
    status: Literal["site_capacity_updated"] = "site_capacity_updated"
    business: BusinessReference
    site_capacity: SiteCapacitySummary


class BusinessActivationChecks(BaseModel):
    has_active_subscription: bool
    has_active_business_owner: bool
    has_active_site: bool


class BusinessActivateResponse(BaseModel):
    status: Literal["business_activated"] = "business_activated"
    business: BusinessView
    activation_checks: BusinessActivationChecks


class BusinessUserSuspendResponse(BaseModel):
    status: Literal["user_suspended"] = "user_suspended"
    business: BusinessReference
    user: MembershipUserSummary
    revoked_session_count: int
    revoked_refresh_token_count: int


class BusinessUserReactivateResponse(BaseModel):
    status: Literal["user_reactivated"] = "user_reactivated"
    business: BusinessReference
    user: MembershipUserSummary
