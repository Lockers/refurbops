from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CollectionNames:
    organisations: str = 'organisations'
    businesses: str = 'businesses'
    sites: str = 'sites'
    users: str = 'users'
    memberships: str = 'memberships'
    subscriptions: str = 'subscriptions'
    subscription_history: str = 'subscription_history'
    entitlements: str = 'entitlements'
    public_applications: str = 'public_applications'
    plan_catalog: str = 'plan_catalog'
    addon_catalog: str = 'addon_catalog'
    entitlement_catalog: str = 'entitlement_catalog'
    auth_credentials: str = 'auth_credentials'
    auth_sessions: str = 'auth_sessions'
    auth_refresh_tokens: str = 'auth_refresh_tokens'
    user_invites: str = 'user_invites'
    email_verifications: str = 'email_verifications'
    password_resets: str = 'password_resets'
    mfa_enrollments: str = 'mfa_enrollments'
    mfa_recovery_codes: str = 'mfa_recovery_codes'
    email_outbox: str = 'email_outbox'
    email_delivery_events: str = 'email_delivery_events'
    email_suppressions: str = 'email_suppressions'
    audit_logs: str = 'audit_logs'
    jobs: str = 'jobs'
    support_tickets: str = 'support_tickets'
    raw_integration_payloads: str = 'raw_integration_payloads'


COLLECTIONS = CollectionNames()
