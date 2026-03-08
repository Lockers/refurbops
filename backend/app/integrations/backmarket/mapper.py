from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


BACKMARKET_SOURCE = "backmarket_buyback"


def map_buyback_order_payload(
    *,
    business_id: str,
    payload: dict[str, Any],
    existing_local_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Map a Back Market buyback order payload into the canonical inbound order shape.

    Rules:
    - `source` is always `backmarket_buyback`
    - `source_reference` comes from `orderPublicId`
    - external payload fields are normalized to snake_case
    - `local_state` must be preserved across re-syncs
    - `raw_payload` is stored for traceability and debugging
    """
    now = datetime.now(UTC)

    return {
        "business_id": business_id,
        "source": BACKMARKET_SOURCE,
        "source_reference": payload.get("orderPublicId"),
        "external_status": payload.get("status"),
        "market": payload.get("market"),
        "creation_date": _parse_datetime(payload.get("creationDate")),
        "modification_date": _parse_datetime(payload.get("modificationDate")),
        "shipping_date": _parse_datetime(payload.get("shippingDate")),
        "suspension_date": _parse_datetime(payload.get("suspensionDate")),
        "receival_date": _parse_datetime(payload.get("receivalDate")),
        "payment_date": _parse_datetime(payload.get("paymentDate")),
        "counter_proposal_date": _parse_datetime(payload.get("counterProposalDate")),
        "listing": {
            "sku": _get_nested(payload, "listing", "sku"),
            "product_id": _coerce_int(_get_nested(payload, "listing", "productId")),
            "title": _get_nested(payload, "listing", "title"),
            "grade": _get_nested(payload, "listing", "grade"),
        },
        "customer": {
            "first_name": _get_nested(payload, "customer", "firstName"),
            "last_name": _get_nested(payload, "customer", "lastName"),
            "phone": _get_nested(payload, "customer", "phone"),
            "date_of_birth": _get_nested(payload, "customer", "dateOfBirth"),
            "documents": _get_nested(payload, "customer", "documents") or [],
        },
        "return_address": {
            "address1": _get_nested(payload, "returnAddress", "address1"),
            "address2": _get_nested(payload, "returnAddress", "address2"),
            "city": _get_nested(payload, "returnAddress", "city"),
            "zipcode": _get_nested(payload, "returnAddress", "zipcode"),
            "country": _get_nested(payload, "returnAddress", "country"),
        },
        "original_price": {
            "value": _coerce_float(_get_nested(payload, "originalPrice", "value")),
            "currency": _get_nested(payload, "originalPrice", "currency"),
        },
        "counter_offer_price": _map_optional_price_block(payload.get("counterOfferPrice")),
        "tracking": {
            "shipper": payload.get("shipper"),
            "tracking_number": payload.get("trackingNumber"),
            "tracking_url": None,
            "status_raw": None,
            "status_group": None,
            "last_checked_at": None,
            "last_event_at": None,
            "likely_arrival_bucket": _derive_likely_arrival_bucket(payload),
        },
        "suspend_reasons": payload.get("suspendReasons") or [],
        "counter_offer_reasons": payload.get("counterOfferReasons") or [],
        "local_state": _merge_local_state(existing_local_state),
        "raw_payload": payload,
        "last_seen_in_api": now,
        "last_synced_at": now,
    }


def _merge_local_state(existing_local_state: dict[str, Any] | None) -> dict[str, Any]:
    """
    Preserve RefurbOps-owned workflow state across re-syncs.

    These fields must never be overwritten by the Back Market payload.
    """
    state = existing_local_state or {}

    return {
        "arrived_clicked": bool(state.get("arrived_clicked", False)),
        "device_created": bool(state.get("device_created", False)),
        "linked_device_id": state.get("linked_device_id"),
        "hidden_from_inbound": bool(state.get("hidden_from_inbound", False)),
        "archived": bool(state.get("archived", False)),
    }


def _map_optional_price_block(value: Any) -> dict[str, Any] | None:
    """
    Normalize an optional Back Market price block.

    Returns None when the source block is missing entirely.
    """
    if not isinstance(value, dict):
        return None

    return {
        "value": _coerce_float(value.get("value")),
        "currency": value.get("currency"),
    }


def _derive_likely_arrival_bucket(payload: dict[str, Any]) -> str | None:
    """
    Derive a simple initial arrival bucket from the Back Market payload alone.

    This is intentionally conservative in Module 01:
    - No tracking number -> not_shipped
    - Tracking number present -> in_transit
    - Everything richer will come later from carrier polling
    """
    tracking_number = payload.get("trackingNumber")
    if not tracking_number:
        return "not_shipped"

    return "in_transit"


def _get_nested(payload: dict[str, Any], parent_key: str, child_key: str) -> Any:
    """
    Safely read a nested value from a payload dictionary.
    """
    parent = payload.get(parent_key)
    if not isinstance(parent, dict):
        return None
    return parent.get(child_key)


def _parse_datetime(value: Any) -> datetime | None:
    """
    Parse an ISO-like Back Market datetime string into a Python datetime.

    Back Market examples include timezone-aware strings such as
    `2019-03-21T14:28:30+01:00`

    Returns None when the value is missing or invalid.
    """
    if not value or not isinstance(value, str):
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _coerce_int(value: Any) -> int | None:
    """
    Convert a value to int when possible, otherwise return None.
    """
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    """
    Convert a value to float when possible, otherwise return None.
    """
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None
