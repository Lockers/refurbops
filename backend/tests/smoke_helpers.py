from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pyotp
from pymongo.database import Database


@dataclass(frozen=True, slots=True)
class SmokeSettings:
    api_base_url: str
    mongo_uri: str
    mongo_db_name: str
    platform_owner_email: str
    platform_owner_password: str
    business_owner_email: str
    business_owner_password: str


@dataclass(slots=True)
class AuthenticatedActor:
    email: str
    password: str
    user_public_id: str
    session_public_id: str
    client: httpx.Client
    organisation_public_ids: list[str]
    business_public_ids: list[str]
    primary_business_public_id: str | None
    site_public_ids: list[str]


_COLLECTION_USERS = "users"
_COLLECTION_MFA_ENROLLMENTS = "mfa_enrollments"
_COLLECTION_AUTH_SESSIONS = "auth_sessions"
_COLLECTION_AUDIT_LOGS = "audit_logs"



def create_authenticated_actor(
    *,
    smoke_settings: SmokeSettings,
    mongo_db: Database[Any],
    email: str,
    password: str,
) -> AuthenticatedActor:
    user = mongo_db[_COLLECTION_USERS].find_one({"email": email})
    assert user is not None, f"User not found in Mongo for email={email}"

    secret = get_active_mfa_secret(mongo_db, user_public_id=str(user["public_id"]), user_email=email)

    client = httpx.Client(base_url=smoke_settings.api_base_url, timeout=30.0, follow_redirects=True)
    code = pyotp.TOTP(secret).now()
    response = client.post(
        "/auth/session/create",
        json={"email": email, "password": password, "code": code},
    )
    assert response.status_code == 200, response.text

    session_response = client.get("/auth/session")
    assert session_response.status_code == 200, session_response.text
    session_payload = session_response.json()
    tenant_context = session_payload.get("tenant_context", {})

    return AuthenticatedActor(
        email=email,
        password=password,
        user_public_id=str(session_payload["user"]["public_id"]),
        session_public_id=str(session_payload["session"]["public_id"]),
        client=client,
        organisation_public_ids=list(tenant_context.get("organisation_public_ids", [])),
        business_public_ids=list(tenant_context.get("business_public_ids", [])),
        primary_business_public_id=tenant_context.get("primary_business_public_id"),
        site_public_ids=list(tenant_context.get("site_public_ids", [])),
    )



def new_unauthenticated_client(smoke_settings: SmokeSettings) -> httpx.Client:
    return httpx.Client(base_url=smoke_settings.api_base_url, timeout=30.0, follow_redirects=True)


def assert_correlation_header(headers: Any) -> str:
    correlation_id = headers.get("x-correlation-id")
    assert correlation_id, f"Missing x-correlation-id header: {headers}"
    return str(correlation_id)


def assert_reason_code(response: httpx.Response, *, expected_reason_code: str) -> dict[str, Any]:
    payload = response.json()
    detail = payload["detail"]
    assert detail["reason_code"] == expected_reason_code, payload
    return detail


def get_active_mfa_secret(mongo_db: Database[Any], *, user_public_id: str, user_email: str | None = None) -> str:
    enrollment = mongo_db[_COLLECTION_MFA_ENROLLMENTS].find_one({"user_id": user_public_id, "status": "active"})
    label = user_email or user_public_id
    assert enrollment is not None, f"Active MFA enrollment missing for user={label}"
    secret = str(enrollment.get("secret", "")).strip()
    assert secret, f"Active MFA secret missing for user={label}"
    return secret


def get_latest_audit(
    mongo_db: Database[Any],
    *,
    event_type: str,
    entity_public_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any] | None:
    query: dict[str, Any] = {"event_type": event_type}
    if entity_public_id is not None:
        query["entity_public_id"] = entity_public_id
    if correlation_id is not None:
        query["correlation_id"] = correlation_id
    return mongo_db[_COLLECTION_AUDIT_LOGS].find_one(query, sort=[("created_at", -1)])



def stale_session_for_sensitive_reauth(mongo_db: Database[Any], *, session_public_id: str) -> None:
    stale_time = datetime.now(UTC) - timedelta(minutes=15)
    mongo_db[_COLLECTION_AUTH_SESSIONS].update_one(
        {"public_id": session_public_id},
        {
            "$set": {
                "mfa_verified_at": stale_time,
                "reauthenticated_at": stale_time,
                "updated_at": datetime.now(UTC),
            }
        },
    )
