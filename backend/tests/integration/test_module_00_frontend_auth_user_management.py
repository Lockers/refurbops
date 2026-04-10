from __future__ import annotations

from typing import Any
from uuid import uuid4

import pyotp
import pytest
from pymongo.database import Database

from tests.smoke_helpers import (
    AuthenticatedActor,
    SmokeSettings,
    assert_correlation_header,
    assert_reason_code,
    get_active_mfa_secret,
    get_latest_audit,
    stale_session_for_sensitive_reauth,
)


pytestmark = [pytest.mark.smoke]


def _create_business_membership(
    business_owner_session: AuthenticatedActor,
    *,
    email: str,
    display_name: str,
    role: str = "manager",
    scope_type: str = "business",
    scope_public_id: str | None = None,
) -> tuple[dict[str, Any], str]:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id, "business_owner session did not resolve a primary business"

    payload: dict[str, Any] = {
        "email": email,
        "display_name": display_name,
        "role": role,
        "scope_type": scope_type,
    }
    if scope_public_id:
        payload["scope_public_id"] = scope_public_id

    response = business_owner_session.client.post(
        f"/foundation/businesses/{business_public_id}/memberships",
        json=payload,
    )
    assert response.status_code == 200, response.text
    correlation_id = assert_correlation_header(response.headers)
    return response.json(), correlation_id



def test_membership_create_requires_display_name_for_new_user_shell(
    business_owner_session: AuthenticatedActor,
    unique_email: str,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    response = business_owner_session.client.post(
        f"/foundation/businesses/{business_public_id}/memberships",
        json={
            "email": unique_email,
            "role": "manager",
            "scope_type": "business",
        },
    )
    assert response.status_code == 422, response.text
    assert_correlation_header(response.headers)
    assert response.json()["detail"] == "display_name is required when creating a new tenant user shell"



def test_membership_create_duplicate_active_membership_returns_conflict_reason_code(
    business_owner_session: AuthenticatedActor,
    unique_email: str,
) -> None:
    created, _ = _create_business_membership(
        business_owner_session,
        email=unique_email,
        display_name="Frontend Duplicate Membership",
    )
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    duplicate = business_owner_session.client.post(
        f"/foundation/businesses/{business_public_id}/memberships",
        json={
            "email": unique_email,
            "display_name": "Frontend Duplicate Membership",
            "role": created["membership"]["role"],
            "scope_type": created["membership"]["scope_type"],
        },
    )
    assert duplicate.status_code == 409, duplicate.text
    assert_correlation_header(duplicate.headers)
    detail = assert_reason_code(duplicate, expected_reason_code="membership_already_exists")
    assert detail["message"] == "Matching active membership already exists"



def test_invite_create_duplicate_pending_invite_returns_conflict_reason_code(
    business_owner_session: AuthenticatedActor,
    unique_email: str,
) -> None:
    created, _ = _create_business_membership(
        business_owner_session,
        email=unique_email,
        display_name="Frontend Invite Duplicate",
    )
    user_public_id = created["user"]["public_id"]

    first = business_owner_session.client.post(
        "/auth/invites/create",
        json={"user_public_id": user_public_id},
    )
    assert first.status_code == 200, first.text
    assert_correlation_header(first.headers)

    duplicate = business_owner_session.client.post(
        "/auth/invites/create",
        json={"user_public_id": user_public_id},
    )
    assert duplicate.status_code == 409, duplicate.text
    assert_correlation_header(duplicate.headers)
    detail = assert_reason_code(duplicate, expected_reason_code="pending_invite_exists")
    assert detail["message"] == "Pending invite already exists"



def test_invite_revoke_without_pending_invite_returns_not_found_reason_code(
    business_owner_session: AuthenticatedActor,
    unique_email: str,
) -> None:
    created, _ = _create_business_membership(
        business_owner_session,
        email=unique_email,
        display_name="Frontend Invite Revoke Missing",
    )
    user_public_id = created["user"]["public_id"]

    response = business_owner_session.client.post(
        "/auth/invites/revoke",
        json={"user_public_id": user_public_id},
    )
    assert response.status_code == 404, response.text
    assert_correlation_header(response.headers)
    detail = assert_reason_code(response, expected_reason_code="pending_invite_not_found")
    assert detail["message"] == "No pending invite to revoke"



def test_membership_add_requires_fresh_reauthentication_when_session_is_stale(
    business_owner_session: AuthenticatedActor,
    mongo_db: Database[Any],
    unique_email: str,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    stale_session_for_sensitive_reauth(
        mongo_db,
        session_public_id=business_owner_session.session_public_id,
    )

    response = business_owner_session.client.post(
        f"/foundation/businesses/{business_public_id}/memberships",
        json={
            "email": unique_email,
            "display_name": "Frontend Reauth Required",
            "role": "manager",
            "scope_type": "business",
        },
    )
    assert response.status_code == 403, response.text
    assert_correlation_header(response.headers)
    detail = assert_reason_code(response, expected_reason_code="sensitive_reauth_required")
    assert detail["message"] == "Fresh reauthentication required"



def test_reauth_requires_mfa_code_for_mfa_protected_user(
    smoke_settings: SmokeSettings,
    platform_owner_session: AuthenticatedActor,
) -> None:
    response = platform_owner_session.client.post(
        "/auth/session/reauth",
        json={"current_password": smoke_settings.platform_owner_password},
    )
    assert response.status_code == 400, response.text
    assert_correlation_header(response.headers)
    detail = assert_reason_code(response, expected_reason_code="missing_reauth_mfa_code")
    assert detail["message"] == "MFA code is required for fresh reauthentication"



def test_reauth_success_returns_valid_until_and_writes_correlated_audit(
    smoke_settings: SmokeSettings,
    mongo_db: Database[Any],
    platform_owner_session: AuthenticatedActor,
) -> None:
    secret = get_active_mfa_secret(
        mongo_db,
        user_public_id=platform_owner_session.user_public_id,
        user_email=platform_owner_session.email,
    )
    code = pyotp.TOTP(secret).now()

    response = platform_owner_session.client.post(
        "/auth/session/reauth",
        json={
            "current_password": smoke_settings.platform_owner_password,
            "code": code,
        },
    )
    assert response.status_code == 200, response.text
    correlation_id = assert_correlation_header(response.headers)
    payload = response.json()
    assert payload["status"] == "session_reauthenticated"
    assert payload["next_step"] == "sensitive_actions_unlocked"
    assert payload["valid_until"]
    assert payload["session"]["reauthenticated_at"]

    audit_row = get_latest_audit(
        mongo_db,
        event_type="auth.session.reauthenticated",
        entity_public_id=platform_owner_session.session_public_id,
        correlation_id=correlation_id,
    )
    assert audit_row is not None, "Expected auth.session.reauthenticated audit row"
    assert audit_row["actor_email"] == platform_owner_session.email



def test_invite_accept_invalid_token_returns_reason_code(
    business_owner_session: AuthenticatedActor,
) -> None:
    response = business_owner_session.client.post(
        "/auth/invites/activate",
        json={
            "invite_token": f"inv_{uuid4().hex}.invalidtoken",
            "password": "FrontendInvalidInvite!123",
        },
    )
    assert response.status_code == 400, response.text
    assert_correlation_header(response.headers)
    detail = assert_reason_code(response, expected_reason_code="invalid_invite_token")
    assert detail["message"] == "Invalid invite token"
