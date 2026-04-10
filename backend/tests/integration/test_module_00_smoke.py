from __future__ import annotations

from typing import Any
from uuid import uuid4

import pyotp
import pytest
from pymongo.database import Database

from tests.smoke_helpers import (
    AuthenticatedActor,
    SmokeSettings,
    get_latest_audit,
    stale_session_for_sensitive_reauth,
)


pytestmark = [pytest.mark.smoke]



def _assert_correlation_header(headers: Any) -> str:
    correlation_id = headers.get("x-correlation-id")
    assert correlation_id, f"Missing x-correlation-id header: {headers}"
    return str(correlation_id)



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



def test_business_owner_session_returns_tenant_context(
    business_owner_session: AuthenticatedActor,
) -> None:
    response = business_owner_session.client.get("/auth/session")
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["status"] == "authenticated"
    assert payload["user"]["email"] == business_owner_session.email
    assert "business_owner" in payload["roles"]
    assert payload["tenant_context"]["primary_business_public_id"]
    assert payload["tenant_context"]["business_public_ids"]
    _assert_correlation_header(response.headers)



def test_business_update_writes_correlated_audit(
    business_owner_session: AuthenticatedActor,
    mongo_db: Database[Any],
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id, "business_owner session did not resolve a primary business"

    new_name = f"Smoke Business {uuid4().hex[:8]}"
    response = business_owner_session.client.patch(
        f"/foundation/businesses/{business_public_id}",
        json={"name": new_name},
    )
    assert response.status_code == 200, response.text
    correlation_id = _assert_correlation_header(response.headers)

    payload = response.json()
    assert payload["status"] == "business_updated"
    assert payload["business"]["name"] == new_name

    audit_row = get_latest_audit(
        mongo_db,
        event_type="foundation.business.updated",
        entity_public_id=business_public_id,
        correlation_id=correlation_id,
    )
    assert audit_row is not None, "Expected correlated foundation.business.updated audit row"
    assert audit_row["business_id"] == business_public_id
    assert audit_row["actor_email"] == business_owner_session.email



def test_read_only_blocks_membership_write_with_reason_code(
    platform_owner_session: AuthenticatedActor,
    business_owner_session: AuthenticatedActor,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id, "business_owner session did not resolve a primary business"

    set_read_only = platform_owner_session.client.patch(
        f"/foundation/businesses/{business_public_id}/subscription",
        json=_subscription_payload(state="past_due"),
    )
    assert set_read_only.status_code == 200, set_read_only.text
    _assert_correlation_header(set_read_only.headers)

    try:
        blocked = business_owner_session.client.post(
            f"/foundation/businesses/{business_public_id}/memberships",
            json={
                "email": f"readonly-smoke-{uuid4().hex[:8]}@repairedtech.co.uk",
                "display_name": "Read Only Smoke",
                "role": "manager",
                "scope_type": "business",
            },
        )
        assert blocked.status_code == 409, blocked.text
        _assert_correlation_header(blocked.headers)
        detail = blocked.json()["detail"]
        assert detail["reason_code"] == "business_read_only"
    finally:
        restore = platform_owner_session.client.patch(
            f"/foundation/businesses/{business_public_id}/subscription",
            json=_subscription_payload(state="active"),
        )
        assert restore.status_code == 200, restore.text
        _assert_correlation_header(restore.headers)



def test_fresh_reauthentication_unlocks_sensitive_action(
    smoke_settings: SmokeSettings,
    mongo_db: Database[Any],
    platform_owner_session: AuthenticatedActor,
    business_owner_session: AuthenticatedActor,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id, "business_owner session did not resolve a primary business"

    stale_session_for_sensitive_reauth(
        mongo_db,
        session_public_id=platform_owner_session.session_public_id,
    )

    blocked = platform_owner_session.client.patch(
        f"/foundation/businesses/{business_public_id}/subscription",
        json=_subscription_payload(state="active"),
    )
    assert blocked.status_code == 403, blocked.text
    _assert_correlation_header(blocked.headers)
    blocked_detail = blocked.json()["detail"]
    assert blocked_detail["reason_code"] == "sensitive_reauth_required"

    enrollment = mongo_db["mfa_enrollments"].find_one(
        {"user_id": platform_owner_session.user_public_id, "status": "active"}
    )
    assert enrollment is not None, "Active MFA enrollment missing for platform owner"
    secret = str(enrollment.get("secret", "")).strip()
    assert secret, "Active MFA secret missing for platform owner"
    code = pyotp.TOTP(secret).now()

    reauth = platform_owner_session.client.post(
        "/auth/session/reauth",
        json={
            "current_password": smoke_settings.platform_owner_password,
            "code": code,
        },
    )
    assert reauth.status_code == 200, reauth.text
    reauth_correlation_id = _assert_correlation_header(reauth.headers)
    reauth_payload = reauth.json()
    assert reauth_payload["status"] == "session_reauthenticated"
    assert reauth_payload["next_step"] == "sensitive_actions_unlocked"

    reauth_audit = get_latest_audit(
        mongo_db,
        event_type="auth.session.reauthenticated",
        entity_public_id=platform_owner_session.session_public_id,
        correlation_id=reauth_correlation_id,
    )
    assert reauth_audit is not None, "Expected correlated auth.session.reauthenticated audit row"
    assert reauth_audit["actor_email"] == platform_owner_session.email

    retried = platform_owner_session.client.patch(
        f"/foundation/businesses/{business_public_id}/subscription",
        json=_subscription_payload(state="active"),
    )
    assert retried.status_code == 200, retried.text
    _assert_correlation_header(retried.headers)
