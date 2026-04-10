from __future__ import annotations

from typing import Any

import httpx
import pytest

from tests.smoke_helpers import AuthenticatedActor, SmokeSettings


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


def test_unauthenticated_session_endpoint_returns_structured_401(smoke_settings: SmokeSettings) -> None:
    with httpx.Client(base_url=smoke_settings.api_base_url, timeout=30.0, follow_redirects=True) as client:
        response = client.get("/auth/session")
    detail = _assert_reason_code(response, status_code=401, reason_code="missing_access_token")
    assert detail["message"] == "Missing access token"


def test_session_refresh_returns_authenticated_payload(
    business_owner_session: AuthenticatedActor,
) -> None:
    response = business_owner_session.client.post("/auth/session/refresh")
    assert response.status_code == 200, response.text
    _assert_correlation_header(response.headers)
    payload = response.json()

    assert payload["status"] == "session_refreshed"
    assert payload["next_step"] == "authenticated"
    assert payload["user"]["email"] == business_owner_session.email
    assert payload["session"]["public_id"]
    assert payload["refresh"]["public_id"]


def test_logout_clears_session_and_blocks_followup_session_read(
    business_owner_session: AuthenticatedActor,
) -> None:
    logout = business_owner_session.client.post("/auth/logout")
    assert logout.status_code == 200, logout.text
    _assert_correlation_header(logout.headers)
    logout_payload = logout.json()
    assert logout_payload["status"] == "logged_out"
    assert logout_payload["next_step"] == "signed_out"

    session_response = business_owner_session.client.get("/auth/session")
    detail = _assert_reason_code(session_response, status_code=401, reason_code="missing_access_token")
    assert detail["message"] == "Missing access token"


def test_platform_and_tenant_authorization_probes_resolve_permissions(
    platform_owner_session: AuthenticatedActor,
    business_owner_session: AuthenticatedActor,
) -> None:
    protected_probe = platform_owner_session.client.get("/auth/protected-probe")
    assert protected_probe.status_code == 200, protected_probe.text
    _assert_correlation_header(protected_probe.headers)
    protected_payload = protected_probe.json()
    assert protected_payload["status"] == "authenticated_request_ok"
    assert protected_payload["user"]["principal_type"] == "platform_owner"

    platform_probe = platform_owner_session.client.get("/auth/authorization-probe")
    assert platform_probe.status_code == 200, platform_probe.text
    _assert_correlation_header(platform_probe.headers)
    platform_payload = platform_probe.json()
    assert platform_payload["status"] == "authorized_request_ok"
    assert platform_payload["required_permission"] == "platform.system_probe"
    assert (
        "platform.system_probe" in platform_payload["effective_permissions"]
        or "*" in platform_payload["effective_permissions"]
    )

    tenant_probe = business_owner_session.client.get("/auth/tenant-authorization-probe")
    assert tenant_probe.status_code == 200, tenant_probe.text
    _assert_correlation_header(tenant_probe.headers)
    tenant_payload = tenant_probe.json()
    assert tenant_payload["status"] == "authorized_request_ok"
    assert tenant_payload["required_permission"] == "tenant.business_owner_probe"
    assert tenant_payload["memberships"]
    assert any(membership["scope_type"] == "business" for membership in tenant_payload["memberships"])
    assert (
        "tenant.business_owner_probe" in tenant_payload["effective_permissions"]
        or "tenant.*" in tenant_payload["effective_permissions"]
        or "business.*" in tenant_payload["effective_permissions"]
    )


def test_tenant_actor_cannot_access_platform_authorization_probe(
    business_owner_session: AuthenticatedActor,
) -> None:
    response = business_owner_session.client.get("/auth/authorization-probe")
    detail = _assert_reason_code(response, status_code=403, reason_code="permission_denied")
    assert detail["context"]["required_permission"] == "platform.system_probe"


def test_reauthentication_requires_authenticated_session(smoke_settings: SmokeSettings) -> None:
    with httpx.Client(base_url=smoke_settings.api_base_url, timeout=30.0, follow_redirects=True) as client:
        response = client.post("/auth/session/reauth", json={"current_password": "wrong-password"})
    detail = _assert_reason_code(response, status_code=401, reason_code="missing_access_token")
    assert detail["message"] == "Missing access token"


def test_reauthentication_invalid_credentials_returns_structured_401(
    platform_owner_session: AuthenticatedActor,
) -> None:
    response = platform_owner_session.client.post(
        "/auth/session/reauth",
        json={"current_password": "definitely-wrong-password"},
    )
    detail = _assert_reason_code(response, status_code=401, reason_code="invalid_reauth_credentials")
    assert detail["message"] == "Invalid reauthentication credentials"
