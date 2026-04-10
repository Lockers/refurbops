# Backend integration and smoke tests

This backend now includes a live Module 00 integration suite so the main auth, foundation, hardening, and audit flows can be checked without clicking through Swagger.

## Current coverage

The current integration suite runs against the real running backend and the real MongoDB state.

It currently covers:

### Auth and session
- `/auth/login` credential verification step
- `/auth/session` authenticated session enrichment
- structured `401 missing_access_token` on unauthenticated access
- `/auth/session/refresh`
- `/auth/logout`
- `/auth/session/reauth`
- invalid re-auth credentials returning stable reason codes
- `/auth/protected-probe`
- `/auth/authorization-probe`
- `/auth/tenant-authorization-probe`

### Foundation read and update flows
- organisation read
- business read
- business sites list
- site read
- subscription read
- subscription history read
- business update with correlated audit
- organisation update with correlated audit
- site update with correlated audit

### Lifecycle and security enforcement
- read-only subscription state blocking tenant writes with stable reason codes
- platform-owner-only enforcement on subscription update
- fresh re-auth required for sensitive actions
- fresh re-auth success unlocking the sensitive action again

### Membership and invite lifecycle
- membership add with correlated audit
- membership archive with correlated audit
- invite create with scoped audit
- invite resend with scoped audit
- invite revoke with scoped audit
- invite accept with issuer-scoped audit

### Audit
- correlated audit rows for write actions
- correlation ID propagation from response headers into audit rows
- business audit feed endpoint
- frontend-safe audit feed records
- invalid audit cursor handling
- unauthenticated audit feed access returning structured `401`

## How it works

The suite:
- calls the real API over HTTP
- uses MongoDB directly to verify persisted state and audit rows
- reads active MFA TOTP secrets directly from Mongo for the seeded users

This matches the way Module 00 was validated manually, but makes the checks repeatable.

## Required environment variables

The tests expect the backend to already be running locally.

Mandatory:
- `SMOKE_PLATFORM_OWNER_PASSWORD`
- `SMOKE_BUSINESS_OWNER_PASSWORD`

Optional overrides:
- `SMOKE_API_BASE_URL` (default: `http://localhost:8000`)
- `SMOKE_MONGO_URI` (default: `mongodb://localhost:27017`)
- `SMOKE_MONGO_DB_NAME` (default: `refurbops`)
- `SMOKE_PLATFORM_OWNER_EMAIL` (default: `info@repairedtech.co.uk`)
- `SMOKE_BUSINESS_OWNER_EMAIL` (default: `owner-demo@repairedtech.co.uk`)

## Run the suite

From `backend/`:

```bash
uv run python scripts/run_module_00_smoke.py
```

Equivalent direct pytest command:

```bash
uv run pytest tests/integration -q -s
```

## Important notes

- The suite mutates real local data.
- Several tests intentionally create new membership users, invites, and audit rows.
- The read-only test restores the subscription state back to `active` at the end.
- Passwords should stay in local environment variables and must not be committed.
- This is still an integration/regression suite, not a full property-based or fuzzing harness.

## Recommended next testing expansions

The next strongest improvements are:
- seed-reset or fixture-based disposable test tenants/businesses
- negative-case coverage for every mutable endpoint
- payload-boundary validation coverage for every schema
- session expiry / refresh reuse / revoked token regression cases
- role-matrix coverage for every routed endpoint
- exportable CI mode against an isolated local test database
