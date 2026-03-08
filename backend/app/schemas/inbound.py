from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InboundListing(BaseModel):
    """Normalized listing details from the Back Market buyback order."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    sku: str | None = None
    product_id: int | None = None
    title: str | None = None
    grade: str | None = None


class InboundCustomerDocument(BaseModel):
    """Normalized customer details from the inbound order."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    date_of_birth: str | None = None
    documents: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def full_name(self) -> str:
        """
        Convenience helper for UI/service use.

        This is not persisted separately; it is derived from first/last name.
        """
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(part for part in parts if part).strip()


class InboundReturnAddress(BaseModel):
    """Normalized return address from the inbound order."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    address1: str | None = None
    address2: str | None = None
    city: str | None = None
    zipcode: str | None = None
    country: str | None = None


class InboundPrice(BaseModel):
    """Normalized price block used for original and counter-offer prices."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    value: float | None = None
    currency: str | None = None


class InboundTracking(BaseModel):
    """
    Tracking layer for inbound orders.

    Carrier tracking is only partially used in the first backend slice, but
    the document shape is included now so the collection stays stable.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    shipper: str | None = None
    tracking_number: str | None = None
    tracking_url: str | None = None
    status_raw: str | None = None
    status_group: str | None = None
    last_checked_at: datetime | None = None
    last_event_at: datetime | None = None
    likely_arrival_bucket: str | None = None


class InboundLocalState(BaseModel):
    """
    Local workflow overlay.

    These fields are owned by RefurbOps and must never be overwritten by the
    external Back Market payload during re-sync.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    arrived_clicked: bool = False
    device_created: bool = False
    linked_device_id: str | None = None
    hidden_from_inbound: bool = False
    archived: bool = False


class InboundOrderDocument(BaseModel):
    """
    Canonical inbound order document used by the repository and API layer.

    MongoDB stores `_id` as ObjectId, but API responses expose it as a string.
    The mapper/service layer can populate `_id` when reading from Mongo.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str | None = Field(default=None, alias="_id")

    business_id: str
    source: str
    source_reference: str

    external_status: str | None = None
    market: str | None = None

    creation_date: datetime | None = None
    modification_date: datetime | None = None
    shipping_date: datetime | None = None
    suspension_date: datetime | None = None
    receival_date: datetime | None = None
    payment_date: datetime | None = None
    counter_proposal_date: datetime | None = None

    listing: InboundListing = Field(default_factory=InboundListing)
    customer: InboundCustomerDocument = Field(default_factory=InboundCustomerDocument)
    return_address: InboundReturnAddress = Field(default_factory=InboundReturnAddress)

    original_price: InboundPrice = Field(default_factory=InboundPrice)
    counter_offer_price: InboundPrice | None = None

    tracking: InboundTracking = Field(default_factory=InboundTracking)

    suspend_reasons: list[dict[str, Any]] = Field(default_factory=list)
    counter_offer_reasons: list[dict[str, Any]] = Field(default_factory=list)

    local_state: InboundLocalState = Field(default_factory=InboundLocalState)

    raw_payload: dict[str, Any] = Field(default_factory=dict)

    last_seen_in_api: datetime | None = None
    last_synced_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InboundQueueRow(BaseModel):
    """
    Queue-friendly inbound row DTO.

    The API should return rows already shaped for the frontend instead of
    forcing the UI to rebuild them from the raw nested document every time.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str = Field(alias="_id")
    business_id: str

    source: str
    source_reference: str

    external_status: str | None = None
    market: str | None = None

    listing_title: str | None = None
    listing_grade: str | None = None

    customer_full_name: str | None = None

    original_price_value: float | None = None
    original_price_currency: str | None = None

    shipper: str | None = None
    tracking_number: str | None = None
    tracking_status_group: str | None = None
    likely_arrival_bucket: str | None = None

    shipping_date: datetime | None = None
    modification_date: datetime | None = None

    arrived_clicked: bool = False
    device_created: bool = False
    linked_device_id: str | None = None
    hidden_from_inbound: bool = False

    last_synced_at: datetime | None = None


class InboundSyncRequest(BaseModel):
    """
    Temporary request model for manual sync.

    Until auth/tenant context exists, business_id is supplied explicitly.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    business_id: str


class InboundSyncResult(BaseModel):
    """Summary returned after a manual Back Market sync run."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    business_id: str
    source: str
    fetched: int
    inserted: int
    updated: int
    started_at: datetime
    completed_at: datetime
    sync_from: datetime | None = None


class InboundListResponse(BaseModel):
    """Paginated inbound queue response."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    items: list[InboundQueueRow]
    total: int
    page: int
    page_size: int
