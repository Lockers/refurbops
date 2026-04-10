from pymongo import ASCENDING, IndexModel

from app.db.collections import COLLECTIONS


INDEX_DEFINITIONS: dict[str, list[IndexModel]] = {
    COLLECTIONS.organisations: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_organisations_public_id"),
    ],
    COLLECTIONS.businesses: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_businesses_public_id"),
        IndexModel([("organisation_id", ASCENDING), ("state", ASCENDING)], name="ix_business_org_state"),
    ],
    COLLECTIONS.sites: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_sites_public_id"),
        IndexModel([("business_id", ASCENDING), ("state", ASCENDING)], name="ix_site_business_state"),
    ],
    COLLECTIONS.subscriptions: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_subscriptions_public_id"),
        IndexModel([("business_id", ASCENDING)], unique=True, name="uq_subscriptions_business_id"),
        IndexModel([("organisation_id", ASCENDING), ("state", ASCENDING)], name="ix_subscriptions_org_state"),
    ],
    COLLECTIONS.subscription_history: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_subscription_history_public_id"),
        IndexModel([("business_id", ASCENDING), ("recorded_at", ASCENDING)], name="ix_subscription_history_business_recorded_at"),
        IndexModel([("subscription_public_id", ASCENDING), ("recorded_at", ASCENDING)], name="ix_subscription_history_subscription_recorded_at"),
    ],
    COLLECTIONS.users: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_users_public_id"),
        IndexModel([("email", ASCENDING)], unique=True, name="uq_users_email"),
        IndexModel(
            [("principal_type", ASCENDING)],
            unique=True,
            name="uq_single_platform_owner",
            partialFilterExpression={"principal_type": "platform_owner"},
        ),
        IndexModel([("organisation_id", ASCENDING), ("state", ASCENDING)], name="ix_users_org_state"),
    ],
    COLLECTIONS.memberships: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_memberships_public_id"),
        IndexModel(
            [("user_id", ASCENDING), ("scope_type", ASCENDING), ("scope_id", ASCENDING), ("role", ASCENDING)],
            unique=True,
            name="uq_membership_user_scope_role",
            partialFilterExpression={"archived_at": None},
        ),
        IndexModel([("organisation_id", ASCENDING), ("scope_type", ASCENDING), ("scope_id", ASCENDING)], name="ix_membership_scope"),
        IndexModel([("scope_id", ASCENDING), ("role", ASCENDING), ("archived_at", ASCENDING)], name="ix_membership_scope_role_archived"),
    ],
    COLLECTIONS.auth_credentials: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_auth_credentials_public_id"),
        IndexModel([("user_id", ASCENDING)], unique=True, name="uq_auth_credentials_user_id"),
    ],
    COLLECTIONS.user_invites: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_user_invites_public_id"),
        IndexModel([("token_hash", ASCENDING)], unique=True, name="uq_user_invites_token_hash"),
        IndexModel([("user_id", ASCENDING), ("state", ASCENDING)], name="ix_user_invites_user_state"),
        IndexModel([("expires_at", ASCENDING)], name="ix_user_invites_expires_at"),
    ],
    COLLECTIONS.mfa_enrollments: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_mfa_enrollments_public_id"),
        IndexModel([("user_id", ASCENDING)], unique=True, name="uq_mfa_enrollments_user_id"),
        IndexModel([("status", ASCENDING)], name="ix_mfa_enrollments_status"),
    ],
    COLLECTIONS.mfa_recovery_codes: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_mfa_recovery_codes_public_id"),
        IndexModel([("user_id", ASCENDING), ("used_at", ASCENDING)], name="ix_mfa_recovery_codes_user_used"),
    ],
    COLLECTIONS.auth_sessions: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_auth_sessions_public_id"),
        IndexModel([("user_id", ASCENDING), ("revoked_at", ASCENDING)], name="ix_sessions_user_revoked"),
        IndexModel([("idle_expires_at", ASCENDING)], name="ix_sessions_idle_expires_at"),
        IndexModel([("absolute_expires_at", ASCENDING)], name="ix_sessions_absolute_expires_at"),
        IndexModel([("refresh_family_id", ASCENDING)], name="ix_sessions_refresh_family_id"),
    ],
    COLLECTIONS.auth_refresh_tokens: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_auth_refresh_tokens_public_id"),
        IndexModel([("token_hash", ASCENDING)], unique=True, name="uq_auth_refresh_tokens_token_hash"),
        IndexModel([("session_id", ASCENDING)], name="ix_auth_refresh_tokens_session_id"),
        IndexModel([("family_id", ASCENDING), ("state", ASCENDING)], name="ix_auth_refresh_tokens_family_state"),
        IndexModel([("expires_at", ASCENDING)], name="ix_auth_refresh_tokens_expires_at"),
        IndexModel([("user_id", ASCENDING), ("revoked_at", ASCENDING)], name="ix_auth_refresh_tokens_user_revoked"),
    ],
    COLLECTIONS.public_applications: [
        IndexModel([("email", ASCENDING)], name="ix_applications_email"),
        IndexModel([("email", ASCENDING)], unique=True, name="uq_open_application_email", partialFilterExpression={"is_open": True}),
    ],
    COLLECTIONS.audit_logs: [
        IndexModel([("public_id", ASCENDING)], unique=True, name="uq_audit_logs_public_id"),
        IndexModel([("business_id", ASCENDING), ("created_at", ASCENDING)], name="ix_audit_logs_business_created_at"),
        IndexModel([("organisation_id", ASCENDING), ("created_at", ASCENDING)], name="ix_audit_logs_organisation_created_at"),
        IndexModel([("entity_type", ASCENDING), ("entity_public_id", ASCENDING), ("created_at", ASCENDING)], name="ix_audit_logs_entity_created_at"),
    ],
    COLLECTIONS.jobs: [
        IndexModel([("business_id", ASCENDING), ("status", ASCENDING)], name="ix_jobs_business_status"),
        IndexModel([("correlation_id", ASCENDING)], name="ix_jobs_correlation_id"),
        IndexModel([("idempotency_key", ASCENDING)], unique=True, name="uq_jobs_idempotency_key"),
    ],
}


async def ensure_indexes(database):
    for collection_name, index_models in INDEX_DEFINITIONS.items():
        if not index_models:
            continue
        await database[collection_name].create_indexes(index_models)
