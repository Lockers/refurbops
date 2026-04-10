from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BusinessReference(BaseModel):
    public_id: str
    name: str


class SiteCapacityMirrorView(BaseModel):
    included_site_limit: int
    additional_site_slots: int
    effective_site_limit: int


class SubscriptionEntitlementsView(BaseModel):
    backmarket_enabled: bool
    pricer_enabled: bool
    kpi_intelligence_enabled: bool
    parts_intelligence_enabled: bool
    included_site_limit: int
    additional_site_slots: int


class BusinessSubscriptionView(BaseModel):
    public_id: str
    organisation_id: str
    business_id: str
    state: str
    plan_code: str
    billing_currency: str
    billing_cadence: str
    entitlements: SubscriptionEntitlementsView
    created_at: str
    updated_at: str


class BusinessSubscriptionReadResponse(BaseModel):
    status: Literal["subscription_loaded"] = "subscription_loaded"
    business: BusinessReference
    subscription: BusinessSubscriptionView
    site_capacity: SiteCapacityMirrorView


class BusinessSubscriptionUpsertRequest(BaseModel):
    state: Literal["trial_active", "active", "past_due", "read_only", "cancelled"]
    plan_code: str = Field(min_length=1, max_length=100)
    billing_currency: str = Field(min_length=3, max_length=3)
    billing_cadence: Literal["monthly", "annual"]
    backmarket_enabled: bool = True
    pricer_enabled: bool = False
    kpi_intelligence_enabled: bool = False
    parts_intelligence_enabled: bool = False
    included_site_limit: int = Field(default=1, ge=1, le=1000)
    additional_site_slots: int = Field(default=0, ge=0, le=1000)


class BusinessSubscriptionUpsertResponse(BaseModel):
    status: Literal["subscription_upserted"] = "subscription_upserted"
    business: BusinessReference
    subscription: BusinessSubscriptionView
    site_capacity: SiteCapacityMirrorView


class SubscriptionHistoryEntryView(BaseModel):
    public_id: str
    subscription_public_id: str
    business_id: str
    organisation_id: str
    state: str
    plan_code: str
    billing_currency: str
    billing_cadence: str
    entitlements: SubscriptionEntitlementsView
    change_type: Literal["created", "updated"]
    recorded_at: str


class BusinessSubscriptionHistoryResponse(BaseModel):
    status: Literal["subscription_history_loaded"] = "subscription_history_loaded"
    business: BusinessReference
    history: list[SubscriptionHistoryEntryView]
