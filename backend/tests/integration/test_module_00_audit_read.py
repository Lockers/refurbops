from __future__ import annotations

from typing import Any
from uuid import uuid4

from pymongo.database import Database

from tests.smoke_helpers import AuthenticatedActor, get_latest_audit


def _assert_correlation_header(headers: Any) -> str:
    correlation_id = headers.get("x-correlation-id")
    assert correlation_id, f"Missing x-correlation-id header: {headers}"
    return str(correlation_id)


def test_business_owner_can_read_business_audit_feed(
    business_owner_session: AuthenticatedActor,
    mongo_db: Database[Any],
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id, "business_owner session did not resolve a primary business"

    new_name = f"Audit Feed Smoke {uuid4().hex[:8]}"
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
    assert audit_row is not None, "Expected correlated business update audit row"

    response = business_owner_session.client.get(
        f"/audit/businesses/{business_public_id}/events",
        params={"event_types": ["foundation.business.updated"], "limit": 10},
    )
    assert response.status_code == 200, response.text
    correlation_id = _assert_correlation_header(response.headers)
    payload = response.json()

    assert payload["status"] == "audit_events_loaded"
    assert payload["business_public_id"] == business_public_id
    assert payload["page"]["returned_count"] >= 1
    assert payload["events"], payload

    event = payload["events"][0]
    assert event["event_type"] == "foundation.business.updated"
    assert event["business_id"] == business_public_id
    assert event["entity_public_id"] == business_public_id
    assert event["actor"]["email"] == business_owner_session.email
    assert "actor_session_id" not in event
    assert event["correlation_id"] == update_correlation_id
    assert correlation_id


def test_business_audit_feed_rejects_invalid_before_cursor(
    business_owner_session: AuthenticatedActor,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id, "business_owner session did not resolve a primary business"

    response = business_owner_session.client.get(
        f"/audit/businesses/{business_public_id}/events",
        params={"before": "not-a-real-timestamp"},
    )
    assert response.status_code == 422, response.text
    _assert_correlation_header(response.headers)
    detail = response.json()["detail"]
    assert detail["reason_code"] == "invalid_before_cursor"
