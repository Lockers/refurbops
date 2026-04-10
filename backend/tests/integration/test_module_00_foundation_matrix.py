from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
import pytest
from pymongo.database import Database

from tests.smoke_helpers import AuthenticatedActor, SmokeSettings, get_latest_audit


pytestmark = [pytest.mark.smoke]


def _assert_correlation_header(headers: Any) -> str:
    correlation_id = headers.get("x-correlation-id")
    assert correlation_id, f"Missing x-correlation-id header: {headers}"
    return str(correlation_id)


def _assert_reason_code(response: httpx.Response, *, status_code: int, reason_code: str) -> dict[str, Any]:
    assert response.status_code == status_code, response.text
    _assert_correlation_header(response.headers)
    detail = response.json()["detail"]
    assert detail["reason_code"] == reason_code
    return detail


def _subscription_payload(*, state: str) -> dict[str, Any]:
    return {
        "state": state,
        "plan_code": "base_gbp_monthly",
        "billing_currency": "GBP",
        "billing_cadence": "monthly",
        "backmarket_enabled": True,
        "pricer_enabled": True,
        "kpi_intelligence_enabled": False,
        "parts_intelligence_enabled": False,
        "included_site_limit": 1,
        "additional_site_slots": 0,
    }


def test_business_owner_can_read_core_foundation_resources(
    business_owner_session: AuthenticatedActor,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id
    organisation_public_id = business_owner_session.organisation_public_ids[0]

    business_response = business_owner_session.client.get(f"/foundation/businesses/{business_public_id}")
    assert business_response.status_code == 200, business_response.text
    _assert_correlation_header(business_response.headers)
    business_payload = business_response.json()
    assert business_payload["status"] == "business_loaded"
    assert business_payload["business"]["public_id"] == business_public_id

    sites_response = business_owner_session.client.get(f"/foundation/businesses/{business_public_id}/sites")
    assert sites_response.status_code == 200, sites_response.text
    _assert_correlation_header(sites_response.headers)
    sites_payload = sites_response.json()
    assert sites_payload["status"] == "business_sites_loaded"
    assert sites_payload["business"]["public_id"] == business_public_id
    assert sites_payload["sites"]

    memberships_response = business_owner_session.client.get(f"/foundation/businesses/{business_public_id}/memberships")
    assert memberships_response.status_code == 200, memberships_response.text
    _assert_correlation_header(memberships_response.headers)
    memberships_payload = memberships_response.json()
    assert memberships_payload["status"] == "business_memberships_loaded"
    assert memberships_payload["memberships"]

    subscription_response = business_owner_session.client.get(f"/foundation/businesses/{business_public_id}/subscription")
    assert subscription_response.status_code == 200, subscription_response.text
    _assert_correlation_header(subscription_response.headers)
    subscription_payload = subscription_response.json()
    assert subscription_payload["status"] == "subscription_loaded"
    assert subscription_payload["subscription"]["business_id"] == business_public_id

    history_response = business_owner_session.client.get(f"/foundation/businesses/{business_public_id}/subscription/history")
    assert history_response.status_code == 200, history_response.text
    _assert_correlation_header(history_response.headers)
    history_payload = history_response.json()
    assert history_payload["status"] == "subscription_history_loaded"
    assert history_payload["history"]
    assert all(entry["business_id"] == business_public_id for entry in history_payload["history"])

    organisation_response = business_owner_session.client.get(f"/foundation/organisations/{organisation_public_id}")
    assert organisation_response.status_code == 200, organisation_response.text
    _assert_correlation_header(organisation_response.headers)
    organisation_payload = organisation_response.json()
    assert organisation_payload["status"] == "organisation_loaded"
    assert organisation_payload["organisation"]["public_id"] == organisation_public_id


def test_business_owner_can_read_known_site_endpoint(
    business_owner_session: AuthenticatedActor,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    sites_response = business_owner_session.client.get(f"/foundation/businesses/{business_public_id}/sites")
    assert sites_response.status_code == 200, sites_response.text
    _assert_correlation_header(sites_response.headers)
    site_public_id = str(sites_response.json()["sites"][0]["public_id"])

    site_response = business_owner_session.client.get(f"/foundation/sites/{site_public_id}")
    assert site_response.status_code == 200, site_response.text
    _assert_correlation_header(site_response.headers)
    site_payload = site_response.json()
    assert site_payload["status"] == "site_loaded"
    assert site_payload["site"]["public_id"] == site_public_id
    assert site_payload["site"]["business_id"] == business_public_id


def test_tenant_owner_cannot_update_subscription(
    business_owner_session: AuthenticatedActor,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    response = business_owner_session.client.patch(
        f"/foundation/businesses/{business_public_id}/subscription",
        json=_subscription_payload(state="active"),
    )
    detail = _assert_reason_code(response, status_code=403, reason_code="platform_owner_required")
    assert detail["message"] == "Platform owner access required"


def test_tenant_owner_cannot_update_site_capacity(
    business_owner_session: AuthenticatedActor,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    response = business_owner_session.client.patch(
        f"/foundation/businesses/{business_public_id}/site-capacity",
        json={"additional_site_slots": 1},
    )
    detail = _assert_reason_code(response, status_code=403, reason_code="platform_owner_required")
    assert detail["message"] == "Platform owner access required"


def test_audit_read_requires_authenticated_session(
    smoke_settings: SmokeSettings,
    business_owner_session: AuthenticatedActor,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    with httpx.Client(base_url=smoke_settings.api_base_url, timeout=30.0, follow_redirects=True) as client:
        response = client.get(f"/audit/businesses/{business_public_id}/events")
    detail = _assert_reason_code(response, status_code=401, reason_code="missing_access_token")
    assert detail["message"] == "Missing access token"


def test_audit_read_event_type_filter_returns_frontend_safe_events(
    business_owner_session: AuthenticatedActor,
    mongo_db: Database[Any],
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    new_name = f"Audit Matrix {uuid4().hex[:8]}"
    update = business_owner_session.client.patch(
        f"/foundation/businesses/{business_public_id}",
        json={"name": new_name},
    )
    assert update.status_code == 200, update.text
    update_correlation_id = _assert_correlation_header(update.headers)

    audit_row = get_latest_audit(
        mongo_db,
        event_type="foundation.business.updated",
        entity_public_id=business_public_id,
        correlation_id=update_correlation_id,
    )
    assert audit_row is not None, "Expected correlated foundation.business.updated audit row"

    response = business_owner_session.client.get(
        f"/audit/businesses/{business_public_id}/events",
        params={"event_types": ["foundation.business.updated"], "limit": 20},
    )
    assert response.status_code == 200, response.text
    _assert_correlation_header(response.headers)
    payload = response.json()

    assert payload["status"] == "audit_events_loaded"
    assert payload["business_public_id"] == business_public_id
    assert payload["events"]
    assert all(event["event_type"] == "foundation.business.updated" for event in payload["events"])
    assert all("actor_session_id" not in event for event in payload["events"])


def test_organisation_update_writes_correlated_audit(
    business_owner_session: AuthenticatedActor,
    mongo_db: Database[Any],
) -> None:
    organisation_public_id = business_owner_session.organisation_public_ids[0]
    new_name = f"Org Matrix {uuid4().hex[:8]}"

    response = business_owner_session.client.patch(
        f"/foundation/organisations/{organisation_public_id}",
        json={"name": new_name},
    )
    assert response.status_code == 200, response.text
    correlation_id = _assert_correlation_header(response.headers)
    payload = response.json()
    assert payload["status"] == "organisation_updated"
    assert payload["organisation"]["name"] == new_name

    audit_row = get_latest_audit(
        mongo_db,
        event_type="foundation.organisation.updated",
        entity_public_id=organisation_public_id,
        correlation_id=correlation_id,
    )
    assert audit_row is not None, "Expected correlated foundation.organisation.updated audit row"
    assert audit_row["organisation_id"] == organisation_public_id
    assert audit_row["actor_email"] == business_owner_session.email
