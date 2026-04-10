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


def test_business_owner_can_read_current_foundation_entities(
    business_owner_session: AuthenticatedActor,
) -> None:
    organisation_public_id = business_owner_session.organisation_public_ids[0]
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id
    assert business_owner_session.site_public_ids, "No site ids available in tenant context"
    site_public_id = business_owner_session.site_public_ids[0]

    organisation = business_owner_session.client.get(f"/foundation/organisations/{organisation_public_id}")
    assert organisation.status_code == 200, organisation.text
    assert_correlation_header(organisation.headers)
    assert organisation.json()["organisation"]["public_id"] == organisation_public_id

    business = business_owner_session.client.get(f"/foundation/businesses/{business_public_id}")
    assert business.status_code == 200, business.text
    assert_correlation_header(business.headers)
    assert business.json()["business"]["public_id"] == business_public_id

    sites = business_owner_session.client.get(f"/foundation/businesses/{business_public_id}/sites")
    assert sites.status_code == 200, sites.text
    assert_correlation_header(sites.headers)
    assert any(site["public_id"] == site_public_id for site in sites.json()["sites"])

    site = business_owner_session.client.get(f"/foundation/sites/{site_public_id}")
    assert site.status_code == 200, site.text
    assert_correlation_header(site.headers)
    assert site.json()["site"]["public_id"] == site_public_id

    subscription = business_owner_session.client.get(f"/foundation/businesses/{business_public_id}/subscription")
    assert subscription.status_code == 200, subscription.text
    assert_correlation_header(subscription.headers)
    assert subscription.json()["business"]["public_id"] == business_public_id

    subscription_history = business_owner_session.client.get(
        f"/foundation/businesses/{business_public_id}/subscription/history"
    )
    assert subscription_history.status_code == 200, subscription_history.text
    assert_correlation_header(subscription_history.headers)
    assert subscription_history.json()["business"]["public_id"] == business_public_id



def test_membership_add_and_archive_write_correlated_audit(
    business_owner_session: AuthenticatedActor,
    mongo_db: Database,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    unique_email = f"smoke-membership-{uuid4().hex[:10]}@repairedtech.co.uk"
    add = business_owner_session.client.post(
        f"/foundation/businesses/{business_public_id}/memberships",
        json={
            "email": unique_email,
            "display_name": "Smoke Membership Archive",
            "role": "manager",
            "scope_type": "business",
        },
    )
    assert add.status_code == 200, add.text
    add_correlation_id = assert_correlation_header(add.headers)
    add_payload = add.json()
    membership_public_id = add_payload["membership"]["public_id"]
    user_public_id = add_payload["user"]["public_id"]

    added_audit = get_latest_audit(
        mongo_db,
        event_type="foundation.membership.added",
        entity_public_id=membership_public_id,
        correlation_id=add_correlation_id,
    )
    assert added_audit is not None
    assert added_audit["business_id"] == business_public_id
    assert added_audit["target_user_id"] == user_public_id

    archive = business_owner_session.client.delete(
        f"/foundation/businesses/{business_public_id}/memberships/{membership_public_id}"
    )
    assert archive.status_code == 200, archive.text
    archive_correlation_id = assert_correlation_header(archive.headers)

    archived_audit = get_latest_audit(
        mongo_db,
        event_type="foundation.membership.archived",
        entity_public_id=membership_public_id,
        correlation_id=archive_correlation_id,
    )
    assert archived_audit is not None
    assert archived_audit["business_id"] == business_public_id
    assert archived_audit["target_user_id"] == user_public_id



def test_site_update_writes_correlated_audit(
    business_owner_session: AuthenticatedActor,
    mongo_db: Database,
) -> None:
    assert business_owner_session.site_public_ids, "No site ids available in tenant context"
    site_public_id = business_owner_session.site_public_ids[0]
    new_name = f"Smoke Site {uuid4().hex[:8]}"

    response = business_owner_session.client.patch(
        f"/foundation/sites/{site_public_id}",
        json={"name": new_name},
    )
    assert response.status_code == 200, response.text
    correlation_id = assert_correlation_header(response.headers)
    payload = response.json()
    assert payload["status"] == "site_updated"
    assert payload["site"]["name"] == new_name

    audit_row = get_latest_audit(
        mongo_db,
        event_type="foundation.site.updated",
        entity_public_id=site_public_id,
        correlation_id=correlation_id,
    )
    assert audit_row is not None
    assert audit_row["site_id"] == site_public_id
    assert audit_row["business_id"] == payload["site"]["business_id"]



def test_organisation_update_writes_correlated_audit(
    business_owner_session: AuthenticatedActor,
    mongo_db: Database,
) -> None:
    organisation_public_id = business_owner_session.organisation_public_ids[0]
    new_name = f"Smoke Organisation {uuid4().hex[:8]}"

    response = business_owner_session.client.patch(
        f"/foundation/organisations/{organisation_public_id}",
        json={"name": new_name},
    )
    assert response.status_code == 200, response.text
    correlation_id = assert_correlation_header(response.headers)
    payload = response.json()
    assert payload["status"] == "organisation_updated"
    assert payload["organisation"]["name"] == new_name

    audit_row = get_latest_audit(
        mongo_db,
        event_type="foundation.organisation.updated",
        entity_public_id=organisation_public_id,
        correlation_id=correlation_id,
    )
    assert audit_row is not None
    assert audit_row["organisation_id"] == organisation_public_id



def test_audit_feed_requires_authentication(
    smoke_settings: SmokeSettings,
    business_owner_session: AuthenticatedActor,
) -> None:
    business_public_id = business_owner_session.primary_business_public_id
    assert business_public_id

    client = new_unauthenticated_client(smoke_settings)
    try:
        response = client.get(f"/audit/businesses/{business_public_id}/events")
        assert response.status_code == 401, response.text
        assert_correlation_header(response.headers)
        detail = assert_reason_code(response, expected_reason_code="missing_access_token")
        assert detail["message"] == "Missing access token"
    finally:
        client.close()
