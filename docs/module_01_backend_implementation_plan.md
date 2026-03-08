# RefurbOps Platform — Module 01 Backend Implementation Plan

This document defines the backend-only implementation plan for the first real build slice of **Module 01 Inbound Sync**.

This version updates the earlier plan to include a **minimal multi-business/business integration config layer** so that Back Market sync is correctly scoped to a business from day one.

This is **not** full auth or user management.
It is the minimum required to avoid hardcoding Back Market credentials globally and creating churn later.

---

# 1. Goal of This Slice

Implement the first backend slice for inbound buyback orders.

This slice must:

- persist inbound orders in MongoDB
- add inbound schemas/models/repository/service
- add API routes to read inbound orders
- add a sync service skeleton for Back Market buyback orders
- make sync business-scoped using minimal business integration config

This slice does **not** yet include:

- Arrived action
- device creation
- device ID generation
- label generation
- USB enrichment
- diagnostics
- CheckMEND
- inventory creation

---

# 2. Current Backend Scaffold

The current backend scaffold is:

```text
backend/
 ├─ app/
 │  ├─ api/
 │  ├─ core/
 │  ├─ integrations/
 │  ├─ models/
 │  ├─ repositories/
 │  ├─ schemas/
 │  ├─ services/
 │  ├─ utils/
 │  ├─ __init__.py
 │  └─ main.py
 │
 ├─ tests/
 ├─ .env
 ├─ .env.example
 ├─ .python-version
 ├─ pyproject.toml
 ├─ README.md
 ├─ requirements.txt
 └─ requirements-dev.txt
```

This structure should remain unchanged.

---

# 3. Design Decision Added In This Version

## 3.1 Global config vs business config

Keep in global app config only:

- `BACKMARKET_BASE_URL`

Store per business in MongoDB:

- Back Market API key
- Accept-Language
- company name
- integration name
- contact email
- proxy URL
- enabled flag

## 3.2 Why this is required now

The platform is already locked as **multi-business**.

If Back Market credentials are stored globally in `.env`, the implementation will become wrong almost immediately and require a rewrite.

So Module 01 should support:

```text
sync inbound orders for business X
using business X Back Market config
```

---

# 4. Files To Create

## 4.1 API

```text
app/api/inbound_router.py
```

Responsibilities:

- expose inbound read routes
- expose manual sync route
- call service layer only
- no business logic

---

## 4.2 Schemas

```text
app/schemas/inbound.py
app/schemas/business.py
```

### `inbound.py`

Should contain request/response models for:

- inbound order detail
- inbound queue row
- inbound queue response
- inbound sync request
- inbound sync result

### `business.py`

Should contain minimal typed models for:

- Back Market business config
- business integration config block

These are not full business CRUD models yet.

---

## 4.3 Repositories

```text
app/repositories/inbound_order_repository.py
app/repositories/sync_state_repository.py
app/repositories/business_repository.py
```

---

## 4.4 Services

```text
app/services/inbound_sync_service.py
```

Only one service is required in this slice.

---

## 4.5 Back Market integration

Create:

```text
app/integrations/backmarket/
  client.py
  mapper.py
```

---

# 5. Existing Files To Update

## 5.1 `app/main.py`

Update to register the inbound router.

## 5.2 `app/core/config.py`

Update to add:

- `BACKMARKET_BASE_URL`
- optional timeout/retry settings if desired

Do **not** add business-specific API key and user-agent fields here.

## 5.3 `app/core/database.py`

No structural rewrite required.

Optional small update only if named collection helpers are wanted.

---

# 6. Collections Used In This Slice

This slice uses:

```text
businesses
inbound_orders
sync_states
```

---

# 7. Minimal Business Document Shape

Use the existing `businesses` collection and extend it with a Back Market integration config block.

Do **not** introduce a separate `business_integrations` collection yet.

Example:

```json
{
  "_id": "biz_001",
  "name": "RepairedTech Ltd",
  "vat_registered": true,
  "vat_scheme": "margin",
  "vat_period": "quarterly",
  "vat_period_start": "2026-01-01",
  "created_at": "2026-03-01T00:00:00Z",
  "updated_at": "2026-03-01T00:00:00Z",
  "integrations": {
    "backmarket": {
      "enabled": true,
      "api_key": "YOUR_BACKMARKET_API_KEY",
      "accept_language": "en-gb",
      "company_name": "RepairedTech",
      "integration_name": "RefurbOps",
      "contact_email": "ops@repairedtech.co.uk",
      "proxy_url": "http://proxy-url-if-needed"
    }
  }
}
```

---

# 8. Back Market User-Agent Rule

Back Market requires:

```text
BM-{CompanyName}-{IntegrationName};{contact_email}
```

Example:

```text
BM-RepairedTech-RefurbOps;ops@repairedtech.co.uk
```

Store the component parts on the business record and generate the final User-Agent in code.

---

# 9. Inbound Orders Document Shape

Collection:

```text
inbound_orders
```

Document shape:

```json
{
  "business_id": "biz_001",
  "source": "backmarket_buyback",
  "source_reference": "US-24527-ABCDE",

  "external_status": "TO_SEND",
  "market": "FR",

  "creation_date": "2019-03-21T14:28:30+01:00",
  "modification_date": "2019-03-26T08:00:53+01:00",
  "shipping_date": "2019-03-21T14:37:54+01:00",
  "suspension_date": "2019-03-21T14:37:54+01:00",
  "receival_date": "2019-03-21T14:37:54+01:00",
  "payment_date": "2019-03-21T14:38:11+01:00",
  "counter_proposal_date": "2019-03-21T14:37:54+01:00",

  "listing": {
    "sku": "21000021",
    "product_id": 2311,
    "title": "Apple iPhone XS 64 Go",
    "grade": "DIAMOND"
  },

  "customer": {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+33699887766",
    "date_of_birth": "1970-03-21",
    "documents": []
  },

  "return_address": {
    "address1": "10, Downing street",
    "address2": "3rd floor",
    "city": "London",
    "zipcode": "93100",
    "country": "United Kingdom"
  },

  "original_price": {
    "value": 1000,
    "currency": "EUR"
  },

  "counter_offer_price": {
    "value": 900,
    "currency": "EUR"
  },

  "tracking": {
    "shipper": "DHL",
    "tracking_number": "8R41352499203",
    "tracking_url": null,
    "status_raw": null,
    "status_group": null,
    "last_checked_at": null,
    "last_event_at": null,
    "likely_arrival_bucket": null
  },

  "suspend_reasons": [],
  "counter_offer_reasons": [],

  "local_state": {
    "arrived_clicked": false,
    "device_created": false,
    "linked_device_id": null,
    "hidden_from_inbound": false,
    "archived": false
  },

  "raw_payload": {},
  "last_seen_in_api": null,
  "last_synced_at": null,
  "created_at": null,
  "updated_at": null
}
```

---

# 10. Required Indexes

## 10.1 `inbound_orders`

Create these indexes:

- unique: `business_id + source + source_reference`
- `business_id + external_status`
- `business_id + local_state.device_created`
- `business_id + local_state.hidden_from_inbound`
- `business_id + modification_date`
- `business_id + tracking.tracking_number`

## 10.2 `sync_states`

Create these indexes:

- unique `_id`
- `business_id + source`

## 10.3 `businesses`

Minimum requirement:

- unique `_id`

No additional index required for this slice.

---

# 11. Sync State Document Shape

Collection:

```text
sync_states
```

Example:

```json
{
  "_id": "sync_backmarket_buyback_biz_001",
  "business_id": "biz_001",
  "source": "backmarket_buyback",
  "last_successful_sync_at": "2026-03-07T10:00:00Z",
  "last_attempted_sync_at": "2026-03-07T10:01:00Z",
  "last_full_resync_at": null,
  "last_error": null,
  "updated_at": "2026-03-07T10:01:00Z"
}
```

---

# 12. Repository Structure And Responsibilities

## 12.1 `business_repository.py`

Responsibilities:

- get business by id
- get Back Market config block for a business
- validate required config exists

Suggested methods:

```python
get_business(business_id: str) -> dict | None
get_backmarket_config(business_id: str) -> dict | None
```

---

## 12.2 `inbound_order_repository.py`

Responsibilities:

- ensure indexes
- upsert inbound order by unique key
- fetch single inbound order
- fetch queue rows with filters and pagination
- preserve local workflow state on sync

Suggested methods:

```python
ensure_indexes() -> None
upsert_order(order_doc: dict) -> dict
get_by_id(business_id: str, inbound_id: str) -> dict | None
get_by_reference(business_id: str, source: str, source_reference: str) -> dict | None
list_queue(business_id: str, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]
```

---

## 12.3 `sync_state_repository.py`

Responsibilities:

- get sync state
- record attempted sync
- record successful sync
- record sync error

Suggested methods:

```python
get_sync_state(business_id: str, source: str) -> dict | None
record_attempt(business_id: str, source: str, attempted_at: datetime) -> None
record_success(business_id: str, source: str, successful_at: datetime) -> None
record_error(business_id: str, source: str, error: str, attempted_at: datetime) -> None
```

---

# 13. Service Responsibilities

## `inbound_sync_service.py`

This service is the orchestrator.

Responsibilities:

- load business config
- validate Back Market integration is enabled
- read sync state
- calculate effective sync window
- fetch Back Market pages
- map payloads into local docs
- upsert inbound orders
- update sync state
- return sync summary

Suggested public method:

```python
sync_backmarket_buyback(business_id: str) -> dict
```

### Sync rule

Use incremental sync by:

```text
modificationDate
```

### Overlap rule

Use a 24-hour overlap window.

Flow:

```text
read sync state
↓
calculate effective sync_from
↓
fetch Back Market orders page by page
↓
map payloads
↓
upsert inbound_orders
↓
update sync_states
↓
return sync summary
```

---

# 14. Back Market Integration Structure

Create:

```text
app/integrations/backmarket/
  client.py
  mapper.py
```

---

## 14.1 `client.py`

Responsibilities:

- perform HTTP requests to Back Market
- build required headers
- support proxy URL
- support timeout handling
- support response validation
- support pagination
- keep endpoint paths inside integration layer

### Constructor

Suggested shape:

```python
class BackMarketClient:
    def __init__(self, base_url: str, timeout_seconds: float = 30.0):
        ...
```

### Required list method

```python
fetch_buyback_orders(
    *,
    api_key: str,
    accept_language: str,
    user_agent: str,
    proxy_url: str | None,
    modification_date_from: str | None,
    page: int = 1,
) -> dict
```

### Headers required

```text
Content-Type: application/json
Accept: application/json
Accept-Language: COUNTRY_CODE
Authorization: Basic TOKEN
User-Agent: BM-company-integration;email
```

### Base URL rule

`BACKMARKET_BASE_URL` remains global config.

### Endpoint path rule

Keep endpoint paths in the client:

```text
/ws/buyback/v1/orders
/ws/buyback/v1/orders/{buybackOrderId}
```

### Proxy rule

Oxylabs rotation is handled externally by URL.

So for this slice, the client only needs standard proxy URL support.

---

## 14.2 `mapper.py`

Responsibilities:

- convert Back Market camelCase fields to internal snake_case structure
- preserve `local_state` on re-sync
- preserve full `raw_payload`
- map buyback list payload into inbound document shape

Suggested function:

```python
map_buyback_order_payload(
    *,
    business_id: str,
    payload: dict,
    existing_local_state: dict | None = None,
) -> dict
```

Important rule:

The mapper must **not wipe local workflow state**.

---

# 15. API Routes

## 15.1 Manual sync

Route:

```http
POST /api/inbound/backmarket/sync
```

For this temporary pre-auth phase, send business id in the body:

```json
{
  "business_id": "biz_001"
}
```

Response example:

```json
{
  "business_id": "biz_001",
  "source": "backmarket_buyback",
  "fetched": 100,
  "inserted": 80,
  "updated": 20,
  "started_at": "2026-03-08T10:00:00Z",
  "completed_at": "2026-03-08T10:00:20Z",
  "sync_from": "2026-03-07T10:00:00Z"
}
```

---

## 15.2 List inbound queue

Route:

```http
GET /api/inbound
```

Temporary query params:

- `business_id`
- `external_status`
- `market`
- `has_tracking`
- `tracking_status_group`
- `likely_arrival_bucket`
- `arrived_clicked`
- `page`
- `page_size`

Purpose:

- return paginated queue rows for inbound orders

---

## 15.3 Get single inbound order

Route:

```http
GET /api/inbound/{inbound_id}
```

Temporary query params:

- `business_id`

Purpose:

- return a single inbound order detail record

---

# 16. Response DTO Design

The queue endpoint should return row-friendly DTOs.

Each row should include at least:

- inbound order id
- source reference
- customer full name
- listing title
- grade
- external status
- market
- offer price
- shipper
- tracking number
- tracking status group
- likely arrival bucket
- shipping date
- local state summary
- last synced at

Do **not** force the frontend later to reconstruct queue rows from raw nested payloads.

---

# 17. Config Update Rules

## `app/core/config.py`

Add only global Back Market config fields such as:

- `backmarket_base_url`
- optional `backmarket_timeout_seconds`
- optional retry/backoff settings if wanted now

Do **not** add:

- `BACKMARKET_API_KEY`
- `BACKMARKET_ACCEPT_LANGUAGE`
- `BACKMARKET_USER_AGENT`
- `HTTP_PROXY_URL`

Those belong to the business document.

---

# 18. Seed Data Requirement For Local Dev

To test this slice cleanly, seed one test business into Mongo with:

- business id
- business name
- Back Market API key
- accept language
- company name
- integration name
- contact email
- proxy url
- enabled flag

This avoids hardcoding credentials globally and keeps the structure correct.

---

# 19. Recommended Implementation Order

Implement in this order:

1. `app/schemas/business.py`
2. `app/schemas/inbound.py`
3. `app/repositories/business_repository.py`
4. `app/repositories/inbound_order_repository.py`
5. `app/repositories/sync_state_repository.py`
6. `app/integrations/backmarket/client.py`
7. `app/integrations/backmarket/mapper.py`
8. `app/services/inbound_sync_service.py`
9. `app/api/inbound_router.py`
10. update `app/core/config.py`
11. update `app/main.py`

---

# 20. Out Of Scope For This Slice

Still not included in this exact implementation:

- auth/login
- user CRUD
- Arrived action
- device creation
- device ID generation
- label generation
- label printing
- scan-to-open workflow
- diagnostics
- CheckMEND
- devices collection usage

Those come in the next slice.

---

# 21. Final Recommendation

This slice should be implemented as:

```text
business-scoped inbound sync foundation
```

That gives you:

- the correct multi-business architecture
- Mongo persistence for inbound orders
- a clean repository/service split
- Back Market sync skeleton
- no unnecessary rewrites later

Once complete, the next slice should be:

```text
Arrived action
→ device creation
→ device_id generation
→ label generation
```

