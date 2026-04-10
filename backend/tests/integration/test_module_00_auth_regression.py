from __future__ import annotations

from uuid import uuid4

from pymongo.database import Database

from tests.smoke_helpers import (
    AuthenticatedActor,
    SmokeSettings,
    assert_correlation_header,
    assert_reason_code,
    get_latest_audit,
    new_unauthenticated_client,
)


def test_login_verification_returns_expected_next_step(
    smoke_settings: SmokeSettings,
) -> None:
    client = new_unauthenticated_client(smoke_settings)
    try:
        response = client.post(
            "/auth/login",
            json={
                "email": smoke_settings.platform_owner_email,
                "password": smoke_settings.platform_owner_password,
            },
        )
        assert response.status_code == 200, response.text
        assert_correlation_header(response.headers)
        payload = response.json()
        assert payload["status"] == "verified"
        assert payload["next_step"] == "session_issue_ready"
        assert payload["user"]["email"] == smoke_settings.platform_owner_email
        assert payload["user"]["principal_type"] == "platform_owner"
    finally:
        client.close()



def test_missing_access_token_on_current_session_is_structured(
    smoke_settings: SmokeSettings,
) -> None:
    client = new_unauthenticated_client(smoke_settings)
    try:
        response = client.get("/auth/session")
        assert response.status_code == 401, response.text
        assert_correlation_header(response.headers)
        detail = assert_reason_code(response, expected_reason_code="missing_access_token")
        assert detail["message"] == "Missing access token"
    finally:
        client.close()



def test_session_refresh_and_logout_round_trip(
    platform_owner_session: AuthenticatedActor,
) -> None:
    refresh = platform_owner_session.client.post("/auth/session/refresh")
    assert refresh.status_code == 200, refresh.text
    assert_correlation_header(refresh.headers)
    refresh_payload = refresh.json()
    assert refresh_payload["status"] == "session_refreshed"

    session_after_refresh = platform_owner_session.client.get("/auth/session")
    assert session_after_refresh.status_code == 200, session_after_refresh.text
    assert_correlation_header(session_after_refresh.headers)

    logout = platform_owner_session.client.post("/auth/logout")
    assert logout.status_code == 200, logout.text
    assert_correlation_header(logout.headers)
    logout_payload = logout.json()
    assert logout_payload["status"] == "logged_out"

    current = platform_owner_session.client.get("/auth/session")
    assert current.status_code == 401, current.text
    assert_correlation_header(current.headers)
    detail = assert_reason_code(current, expected_reason_code="missing_access_token")
    assert detail["message"] == "Missing access token"



def test_reauth_rejects_invalid_credentials_with_reason_code(
    platform_owner_session: AuthenticatedActor,
) -> None:
    response = platform_owner_session.client.post(
        "/auth/session/reauth",
        json={"current_password": "definitely-not-the-right-password"},
    )
    assert response.status_code == 401, response.text
    assert_correlation_header(response.headers)
    detail = assert_reason_code(response, expected_reason_code="invalid_reauth_credentials")
    assert detail["message"] == "Invalid reauthentication credentials"



def test_business_owner_cannot_update_subscription(
    business_owner_session: AuthenticatedActor,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    response = business_owner_session.client.patch(
        f"/foundation/businesses/{business_public_id}/subscription",
        json={
            "state": "active",
            "plan_code": "base_gbp_monthly",
            "billing_currency": "GBP",
            "billing_cadence": "monthly",
            "backmarket_enabled": True,
            "pricer_enabled": True,
            "kpi_intelligence_enabled": False,
            "parts_intelligence_enabled": False,
            "included_site_limit": 1,
            "additional_site_slots": 0,
        },
    )
    assert response.status_code == 403, response.text
    assert_correlation_header(response.headers)
    detail = assert_reason_code(response, expected_reason_code="platform_owner_required")
    assert detail["message"] == "Platform owner access required"



def test_invite_activation_writes_correlated_accept_audit(
    business_owner_session: AuthenticatedActor,
    mongo_db: Database,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    unique_email = f"smoke-invite-{uuid4().hex[:10]}@repairedtech.co.uk"
    membership_add = business_owner_session.client.post(
        f"/foundation/businesses/{business_public_id}/memberships",
        json={
            "email": unique_email,
            "display_name": "Smoke Invite Acceptance",
            "role": "manager",
            "scope_type": "business",
        },
    )
    assert membership_add.status_code == 200, membership_add.text
    assert_correlation_header(membership_add.headers)
    membership_payload = membership_add.json()
    user_public_id = membership_payload["user"]["public_id"]

    create_invite = business_owner_session.client.post(
        "/auth/invites/create",
        json={
            "user_public_id": user_public_id,
            "email": unique_email,
        },
    )
    assert create_invite.status_code == 200, create_invite.text
    create_correlation_id = assert_correlation_header(create_invite.headers)
    invite_payload = create_invite.json()
    invite_public_id = invite_payload["invite"]["public_id"]
    invite_token = invite_payload["invite_token"]

    invite_created_audit = get_latest_audit(
        mongo_db,
        event_type="auth.invite.created",
        entity_public_id=invite_public_id,
        correlation_id=create_correlation_id,
    )
    assert invite_created_audit is not None
    assert invite_created_audit["business_id"] == business_public_id

    activate = business_owner_session.client.post(
        "/auth/invites/activate",
        json={
            "invite_token": invite_token,
            "password": f"SmokeAccept!{uuid4().hex[:8]}Aa1",
        },
    )
    assert activate.status_code == 200, activate.text
    activate_correlation_id = assert_correlation_header(activate.headers)
    activate_payload = activate.json()
    assert activate_payload["status"] == "invite_accepted"
    assert activate_payload["user"]["state"] == "active"

    accepted_audit = get_latest_audit(
        mongo_db,
        event_type="auth.invite.accepted",
        entity_public_id=invite_public_id,
        correlation_id=activate_correlation_id,
    )
    assert accepted_audit is not None
    assert accepted_audit["business_id"] == business_public_id
    assert accepted_audit["target_user_id"] == user_public_id
    assert accepted_audit["metadata"]["audit_scope_source"] == "invite_issuer"
    assert accepted_audit["metadata"]["target_scope_snapshot"]["business_public_id"] == business_public_id


def test_invite_create_resend_revoke_write_scoped_audit(
    business_owner_session: AuthenticatedActor,
    mongo_db: Database,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    unique_email = f"smoke-invite-revoke-{uuid4().hex[:10]}@repairedtech.co.uk"
    membership_add = business_owner_session.client.post(
        f"/foundation/businesses/{business_public_id}/memberships",
        json={
            "email": unique_email,
            "display_name": "Smoke Invite Revoke",
            "role": "manager",
            "scope_type": "business",
        },
    )
    assert membership_add.status_code == 200, membership_add.text
    assert_correlation_header(membership_add.headers)
    user_public_id = membership_add.json()["user"]["public_id"]

    create = business_owner_session.client.post(
        "/auth/invites/create",
        json={"user_public_id": user_public_id, "email": unique_email},
    )
    assert create.status_code == 200, create.text
    create_correlation_id = assert_correlation_header(create.headers)
    create_payload = create.json()
    created_invite_public_id = create_payload["invite"]["public_id"]

    created_audit = get_latest_audit(
        mongo_db,
        event_type="auth.invite.created",
        entity_public_id=created_invite_public_id,
        correlation_id=create_correlation_id,
    )
    assert created_audit is not None
    assert created_audit["business_id"] == business_public_id
    assert created_audit["target_user_id"] == user_public_id

    resend = business_owner_session.client.post(
        "/auth/invites/resend",
        json={"user_public_id": user_public_id},
    )
    assert resend.status_code == 200, resend.text
    resend_correlation_id = assert_correlation_header(resend.headers)
    resend_payload = resend.json()
    resent_invite_public_id = resend_payload["invite"]["public_id"]

    resent_audit = get_latest_audit(
        mongo_db,
        event_type="auth.invite.resent",
        entity_public_id=resent_invite_public_id,
        correlation_id=resend_correlation_id,
    )
    assert resent_audit is not None
    assert resent_audit["business_id"] == business_public_id
    assert resent_audit["target_user_id"] == user_public_id

    revoke = business_owner_session.client.post(
        "/auth/invites/revoke",
        json={"user_public_id": user_public_id},
    )
    assert revoke.status_code == 200, revoke.text
    revoke_correlation_id = assert_correlation_header(revoke.headers)
    revoke_payload = revoke.json()
    assert revoke_payload["revoked_pending_invite_count"] >= 1

    revoked_audit = get_latest_audit(
        mongo_db,
        event_type="auth.invite.revoked",
        entity_public_id=user_public_id,
        correlation_id=revoke_correlation_id,
    )
    assert revoked_audit is not None
    assert revoked_audit["business_id"] == business_public_id
    assert revoked_audit["target_user_id"] == user_public_id
    assert revoked_audit["metadata"]["revoked_pending_invite_count"] >= 1


def test_platform_and_tenant_authorization_probes_resolve_permissions(
    platform_owner_session: AuthenticatedActor,
    business_owner_session: AuthenticatedActor,
) -> None:
    protected_probe = platform_owner_session.client.get("/auth/protected-probe")
    assert protected_probe.status_code == 200, protected_probe.text
    assert_correlation_header(protected_probe.headers)
    protected_payload = protected_probe.json()
    assert protected_payload["status"] == "authenticated_request_ok"
    assert protected_payload["user"]["principal_type"] == "platform_owner"

    platform_probe = platform_owner_session.client.get("/auth/authorization-probe")
    assert platform_probe.status_code == 200, platform_probe.text
    assert_correlation_header(platform_probe.headers)
    platform_payload = platform_probe.json()
    assert platform_payload["required_permission"] == "platform.system_probe"
    assert (
        "platform.system_probe" in platform_payload["effective_permissions"]
        or "*" in platform_payload["effective_permissions"]
    )

    tenant_probe = business_owner_session.client.get("/auth/tenant-authorization-probe")
    assert tenant_probe.status_code == 200, tenant_probe.text
    assert_correlation_header(tenant_probe.headers)
    tenant_payload = tenant_probe.json()
    assert tenant_payload["status"] == "authorized_request_ok"
    assert tenant_payload["required_permission"] == "tenant.business_owner_probe"
    assert tenant_payload["memberships"]
    assert any(membership["scope_type"] == "business" for membership in tenant_payload["memberships"])
    assert (
        "tenant.business_owner_probe" in tenant_payload["effective_permissions"]
        or "business.*" in tenant_payload["effective_permissions"]
    )
