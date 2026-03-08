# RefurbOps Platform — Module 01 Inbound Sync Spec (Expanded to Include Label Generation)

This document defines the first implementation module for the RefurbOps platform.

This version expands Module 01 so that label generation is included in the first real build slice.

Module 01 now covers:

- BackMarket buyback order sync
- local inbound order storage
- inbound queue API
- inbound queue UI foundation
- Arrived action
- device creation from inbound
- global `device_id` generation
- minimal barcode label generation
- print-preview / browser print flow
- label print confirmation and reprint support

This creates a proper bench-ready intake foundation without requiring a full direct printer bridge on day one.

---

# 1. Module Goal

Build a clean inbound pipeline where BackMarket buyback orders are pulled into the platform, stored locally, shown in a usable inbound queue, and converted into tracked device records when they physically arrive.

The first operational flow should be:

Inbound queue row
→ click **Arrived**
→ create device record
→ assign global `device_id`
→ generate intake barcode label
→ open print preview / print dialog
→ confirm label printed
→ open device record

This keeps intake fast and gives every physical unit an internal identity immediately.

---

# 2. Business Outcome

At the end of Module 01, the business should be able to:

1. manually sync BackMarket buyback orders
2. see a clean inbound queue from local DB data
3. view shipped/tracked items in a more useful queue
4. click **Arrived** on an inbound order
5. automatically create a device record
6. generate a global `device_id`
7. generate a printable barcode label for that `device_id`
8. confirm the label was printed
9. reprint the label later if needed
10. hide the inbound order from the active queue
11. open the created device record

This is the first operational milestone of the new platform.

---

# 3. Scope

## 3.1 Included in Module 01

- BackMarket client
- BackMarket buyback sync service
- sync state persistence
- inbound order upsert logic
- inbound order deduplication
- inbound queue endpoints
- manual sync endpoint
- Arrived endpoint
- device creation from inbound
- `device_id` generation
- minimal intake barcode label generation
- browser/system print-preview flow
- label print confirmation endpoint
- label reprint endpoint
- label metadata persistence on the device record
- frontend inbound queue page foundation
- frontend print flow immediately after Arrived

## 3.2 Explicitly not included in Module 01

- automated scheduled sync
- full resync UI
- direct USB/network printer bridge
- printer queue management / spooler integration
- scan-to-open search input
- USB data capture
- diagnostics
- CheckMEND
- repair flow
- inventory creation
- sales logic
- richer repair / stock label templates

Those come later.

---

# 4. Design Decisions Locked by This Module

## 4.1 Barcode identity rule

The barcode value must be the platform `device_id`, not IMEI, not order number, and not any customer identifier.

Example:

```text
DEV-00000001
```

## 4.2 Device ID format

Use `system_counters` and generate IDs in this format:

```text
DEV-00000001
```

The ID is globally unique across the platform and never changes.

## 4.3 Device record identity

For Module 01, standardise the device record so that:

- `_id = device_id`
- `device_id` is also stored explicitly for clarity in DTOs and cross-collection references

Example:

```json
{
  "_id": "DEV-00000001",
  "device_id": "DEV-00000001"
}
```

This removes ambiguity and makes scanning, linking, and debugging simpler.

## 4.4 Label symbology

Use **Code 128** for the intake label.

## 4.5 Label v1 philosophy

The intake label should stay minimal.

Default intake label content:

- barcode encoding `device_id`
- human-readable `device_id`

Optional small helper line if enabled by config:

- short device title derived from `listing.title`

But the encoded barcode value must remain only `device_id`.

## 4.6 Printing approach for Module 01

Module 01 should support label printing through generated HTML/PDF plus browser or system print.

This means:

- backend generates the printable label document
- frontend opens print preview
- user prints using the workstation/browser/OS

A direct thermal printer bridge can be added later without changing the workflow.

## 4.7 Status handling rule

Device creation and label printing are related but not the same event.

Rule:

- on creation, device status = `arrived`
- after the user confirms the label was printed, move status to `label_printed`
- if print preview generation fails or the user cancels printing, device stays `arrived`
- reprint does not create a new device and does not change the barcode value

This preserves the status model cleanly.

---

# 5. Dependencies

Module 01 depends on:

- Mongo connection
- FastAPI app skeleton
- React frontend skeleton
- docs already agreed:
  - `data_model_v1.md`
  - `status_model_v1.md`
  - `backmarket_inbound_sync_spec_v2.md`
  - `module_plan_v1.md`

---

# 6. Source Naming Standardisation

For this module, the canonical inbound source value is:

```text
backmarket_buyback
```

Use this consistently in code, indexes, and queries.

If any older docs/examples still say `backmarket_tradein`, treat that as legacy wording and do not use it in the implementation.

---

# 7. Backend Collections Used

Module 01 uses these collections:

```text
sync_states
inbound_orders
devices
system_counters
```

No extra collection is required for labels in v1.

Label metadata should live on the device document.

---

# 8. Backend Architecture for Module 01

Recommended backend file structure for this module:

```text
backend/app/
  api/routers/
    inbound_router.py
    label_router.py

  schemas/
    inbound.py
    device.py
    label.py

  services/
    inbound_sync_service.py
    inbound_device_service.py
    device_id_service.py
    device_workflow_service.py
    label_service.py

  repositories/
    inbound_order_repository.py
    device_repository.py
    sync_state_repository.py
    counter_repository.py

  integrations/
    backmarket/
      client.py
      mapper.py
    labels/
      barcode_generator.py
      label_renderer.py
      templates.py

  core/
    config.py
    database.py
```

### Responsibilities

- `inbound_router.py`:
  - sync endpoints
  - queue endpoints
  - Arrived endpoint
- `label_router.py`:
  - render label
  - confirm printed
  - reprint
- `device_workflow_service.py`:
  - controlled status transitions
  - `arrived -> label_printed`
- `label_service.py`:
  - barcode payload generation
  - template data preparation
  - printable document generation
  - label metadata updates
- `integrations/labels/*`:
  - rendering only
  - no business logic

---

# 9. BackMarket Client Responsibilities

File:

```text
backend/app/integrations/backmarket/client.py
```

Responsibilities:

- authenticate with BackMarket API
- call `GET /ws/buyback/v1/orders`
- handle pagination
- support query params
- return raw order payloads

Required method:

```python
fetch_buyback_orders(
    modification_date_from: str | None = None,
    page: int = 1,
) -> dict
```

---

# 10. BackMarket Mapper Responsibilities

File:

```text
backend/app/integrations/backmarket/mapper.py
```

Responsibilities:

- map BackMarket payload into local inbound order structure
- separate parsed fields from raw payload
- preserve local workflow state during upsert
- produce normalized dict for DB write

Important rule:

The mapper must never wipe local workflow state such as:

- `local_state.arrived_clicked`
- `local_state.device_created`
- `local_state.linked_device_id`
- `local_state.hidden_from_inbound`

Those are business-owned state, not external-owned state.

---

# 11. Sync State Service Design

Use `sync_states` collection.

Each business/source pair should have one sync state record.

Example `_id` format:

```text
sync_backmarket_buyback_<business_id>
```

Example:

```text
sync_backmarket_buyback_biz_001
```

Stored fields:

- `business_id`
- `source`
- `last_successful_sync_at`
- `last_attempted_sync_at`
- `last_full_resync_at`
- `last_error`
- `updated_at`

---

# 12. Incremental Sync Logic

## 12.1 Rule

Sync by `modificationDate`.

## 12.2 Flow

```text
read sync state
↓
derive effective_sync_from
↓
call BackMarket with modificationDate >= effective_sync_from
↓
page through all results
↓
upsert inbound orders
↓
update sync state
```

## 12.3 Overlap

Use a 24-hour overlap window.

Example:

```text
effective_sync_from = last_successful_sync_at - 24h
```

If there is no previous successful sync:

- default to a configurable initial lookback window
- recommended initial value: 30 days

---

# 13. Deduplication Rule

Inbound orders must be uniquely identified by:

```text
business_id + source + source_reference
```

Where:

- `source = backmarket_buyback`
- `source_reference = orderPublicId`

Use Mongo upsert logic with this key.

---

# 14. Inbound Order Schema for Module 01

Persist inbound orders with at least these fields:

## Identity

- `_id`
- `business_id`
- `source`
- `source_reference`

## External state

- `external_status`
- `market`
- `creation_date`
- `modification_date`
- `shipping_date`
- `suspension_date`
- `receival_date`
- `payment_date`
- `counter_proposal_date`

## Listing

- `listing.sku`
- `listing.product_id`
- `listing.title`
- `listing.grade`

## Customer

- `customer.first_name`
- `customer.last_name`
- `customer.phone`
- `customer.date_of_birth`
- `customer.documents`

## Return address

- `return_address.address1`
- `return_address.address2`
- `return_address.city`
- `return_address.zipcode`
- `return_address.country`

## Pricing

- `original_price.value`
- `original_price.currency`
- `counter_offer_price.value`
- `counter_offer_price.currency`

## Tracking

- `tracking.shipper`
- `tracking.tracking_number`
- `tracking.tracking_url`
- `tracking.status_raw`
- `tracking.status_group`
- `tracking.last_checked_at`
- `tracking.last_event_at`
- `tracking.likely_arrival_bucket`

## Reasons

- `suspend_reasons`
- `counter_offer_reasons`

## Local workflow state

- `local_state.arrived_clicked`
- `local_state.device_created`
- `local_state.linked_device_id`
- `local_state.hidden_from_inbound`
- `local_state.archived`

## Metadata

- `last_seen_in_api`
- `last_synced_at`
- `raw_payload`
- `created_at`
- `updated_at`

---

# 15. Inbound Queue Query Rules

The default active inbound queue should return orders where:

- `business_id = current business`
- `local_state.device_created = false`
- `local_state.hidden_from_inbound = false`

Additional filters should support:

- external status
- market
- shipper
- has tracking number
- tracking status group
- likely arrival bucket
- arrived clicked

These should be query params on the queue endpoint.

---

# 16. Suggested Queue Views

The frontend can later support named queue tabs/views, but Module 01 should at least support the data needed for:

## Active inbound
Not yet processed into device.

## Shipped
Has tracking number / shipping date.

## Likely arriving soon
Tracking bucket = likely arriving soon or out for delivery.

## Counter proposal
BackMarket external status = `COUNTER_PROPOSAL`.

## Suspended
BackMarket external status = `SUSPENDED`.

## Arrived not processed
`arrived_clicked = true` and `device_created = false`.

---

# 17. Arrived Action Behaviour

The Arrived action is the most important mutation in Module 01.

## 17.1 Trigger

User clicks **Arrived** on an inbound order row.

## 17.2 Required backend behaviour

1. validate inbound order exists for business
2. validate device has not already been created
3. set `local_state.arrived_clicked = true`
4. create a new device record
5. generate global `device_id`
6. copy snapshots from inbound order into device
7. initialize label metadata
8. link device back to inbound order
9. set:
   - `local_state.device_created = true`
   - `local_state.linked_device_id = <device_id>`
   - `local_state.hidden_from_inbound = true`
10. generate label preview data if requested
11. return created device summary and label print payload

## 17.3 Device initial values on creation

Set:

- `status = arrived`
- `status_updated_at = now`
- `route = unknown`
- `location = null`
- `assigned_user_id = null`
- `flags = []`

## 17.4 Transaction boundary rule

Device creation must not depend on a successful print preview/render.

If label generation fails:

- device creation still succeeds
- inbound row still links to the device
- device remains in status `arrived`
- response includes a warning / label generation failure payload
- user can use reprint / generate label again from the device

This prevents intake from failing just because printing has a problem.

---

# 18. Device Creation Mapping

When a device is created from inbound order, map these fields.

## Identity

- `_id = device_id`
- `device_id = device_id`
- `business_id`
- `inbound_order_id`
- `source.type = backmarket_buyback`
- `source.reference = source_reference`

## Customer snapshot

- combine customer first name + last name where useful
- copy return address into a simple snapshot shape
- include phone if useful in the snapshot

## Expected device snapshot

- `model` from `listing.title`
- `condition` from listing grade or external grade mapping
- `buy_price` from `original_price.value`
- other inferred fields may stay null/default until later enrichment

## Financial snapshot

Initialize at least:

- `buy_price = original_price.value`
- `estimated_repair_cost = null`
- `actual_repair_cost = 0`
- `predicted_profit = null`
- `actual_profit = null`

## Sale readiness

Initialize false/default values.

## USB / diagnostics / CheckMEND summaries

Initialize empty/default values.

## Label metadata

Initialize:

```json
{
  "barcode_value": "DEV-00000001",
  "symbology": "code128",
  "template_key": "intake_minimal",
  "generated_at": null,
  "generated_by_user_id": null,
  "print_requested_at": null,
  "last_printed_at": null,
  "last_printed_by_user_id": null,
  "print_count": 0,
  "last_rendered_format": null,
  "last_rendered_path": null
}
```

---

# 19. Device ID Generation

Use `system_counters` collection.

Counter key:

```text
device_id
```

Format result as:

```text
DEV-00000001
```

The device creation service must always use the counter service and must never generate IDs ad hoc.

---

# 20. Label Generation Spec

## 20.1 Purpose

Generate a printable intake label immediately after device creation.

## 20.2 Encoded barcode value

Encoded value must be exactly:

```text
<device_id>
```

Example:

```text
DEV-00000001
```

No IMEI, no order reference, no customer data in the barcode payload.

## 20.3 Default template

Template key:

```text
intake_minimal
```

### Required visible contents

- Code 128 barcode
- human-readable `device_id`

### Optional visible helper line

- short device title from inbound listing if enabled by config

Example minimal layout:

```text
[ CODE128 BARCODE ]
DEV-00000001
```

Example compact-plus layout if helper line is enabled:

```text
[ CODE128 BARCODE ]
DEV-00000001
Apple iPhone XS 64 Go
```

But the barcode itself still encodes only `DEV-00000001`.

## 20.4 Output formats

Module 01 should support:

- HTML print view
- PDF print view

Recommended default:

- PDF for consistency
- HTML allowed for easier early iteration

## 20.5 Label size

Start with a small intake label suitable for device bag / tray usage.

Suggested baseline:

```text
50mm x 25mm
```

Make this configurable.

## 20.6 Print target assumption

Module 01 assumes the workstation can print the generated label document through the OS/browser.

No direct printer SDK or spooler is required yet.

## 20.7 Label attachment rule

Operationally, the intake label should be applied to:

- the phone bag
- the intake tray
- or another removable handling label

Avoid making the workflow depend on sticking labels directly onto the phone body.

---

# 21. Label Metadata and Status Rules

## 21.1 Generate label vs print label

These are separate states.

- **generated** = printable label document exists
- **printed** = user confirmed a physical label was printed

## 21.2 Workflow rule

- device starts at `arrived`
- label render/generation does **not** change status on its own
- confirming a successful print moves the device to `label_printed`
- reprinting a label after that does not change status again

## 21.3 Metadata updates

When label document is generated:

- `label.generated_at = now`
- `label.generated_by_user_id = current user`
- `label.last_rendered_format = pdf|html`
- `label.last_rendered_path = generated file path or URL if persisted`

When print preview is opened / requested:

- `label.print_requested_at = now`

When the user confirms printing:

- `label.last_printed_at = now`
- `label.last_printed_by_user_id = current user`
- `label.print_count += copies_confirmed`

If current status is `arrived`, transition to `label_printed`.

---

# 22. Backend Endpoints for Module 01

## 22.1 Manual inbound sync

**Route**

```http
POST /api/inbound/backmarket/sync
```

**Purpose**

- trigger incremental sync now

**Request**

- no body required initially
- business context comes from auth or temporary business selection

**Response**

- total fetched
- total inserted
- total updated
- sync window used
- sync completed at

---

## 22.2 List inbound queue

**Route**

```http
GET /api/inbound
```

**Query params**

- `external_status`
- `has_tracking`
- `tracking_status_group`
- `likely_arrival_bucket`
- `arrived_clicked`
- `page`
- `page_size`

**Response**

- paginated inbound rows

---

## 22.3 Get single inbound order

**Route**

```http
GET /api/inbound/{inbound_order_id}
```

**Purpose**

- detail drawer/page later
- debugging
- UI row expansion if needed

---

## 22.4 Arrived action

**Route**

```http
POST /api/inbound/{inbound_order_id}/arrive
```

**Purpose**

- perform arrived workflow
- create device
- hide inbound item
- optionally generate label preview immediately
- return device link and print payload

**Suggested request body**

```json
{
  "generate_label": true,
  "label_format": "pdf",
  "label_template_key": "intake_minimal"
}
```

**Response**

```json
{
  "inbound_order": {
    "id": "inb_001",
    "source_reference": "US-24527-ABCDE",
    "hidden_from_inbound": true
  },
  "device": {
    "id": "DEV-00000001",
    "device_id": "DEV-00000001",
    "status": "arrived",
    "route": "unknown"
  },
  "label": {
    "generated": true,
    "template_key": "intake_minimal",
    "barcode_value": "DEV-00000001",
    "format": "pdf",
    "print_url": "/api/labels/devices/DEV-00000001/render?format=pdf"
  },
  "redirect_target": "/devices/DEV-00000001",
  "warnings": []
}
```

If label generation fails but device creation succeeds:

```json
{
  "device": {
    "id": "DEV-00000001",
    "status": "arrived"
  },
  "label": {
    "generated": false,
    "error": "label_render_failed"
  },
  "warnings": ["Device created but label preview could not be generated"]
}
```

---

## 22.5 Render device label

**Route**

```http
GET /api/labels/devices/{device_id}/render
```

**Query params**

- `format=pdf|html`
- `template_key=intake_minimal`
- `force_regenerate=false|true`

**Purpose**

- render printable intake label for preview or reprint

**Response**

- printable document stream, or
- JSON containing a signed/local URL to the printable file

Recommended first implementation:

- return PDF stream directly

---

## 22.6 Confirm label printed

**Route**

```http
POST /api/labels/devices/{device_id}/confirm-printed
```

**Purpose**

- record that a physical label was printed
- update print metadata
- transition status to `label_printed` when appropriate

**Suggested request body**

```json
{
  "copies": 1,
  "print_source": "browser"
}
```

**Response**

```json
{
  "device_id": "DEV-00000001",
  "status": "label_printed",
  "print_count": 1,
  "last_printed_at": "2026-03-07T12:00:00Z"
}
```

---

## 22.7 Reprint label

**Route**

```http
POST /api/labels/devices/{device_id}/reprint
```

**Purpose**

- generate a fresh print preview for an existing device
- does not create a new barcode
- does not create a new device

**Suggested request body**

```json
{
  "format": "pdf",
  "template_key": "intake_minimal"
}
```

**Response**

```json
{
  "device_id": "DEV-00000001",
  "barcode_value": "DEV-00000001",
  "print_url": "/api/labels/devices/DEV-00000001/render?format=pdf&force_regenerate=true"
}
```

---

# 23. Response Shape for Queue Rows

The inbound queue response should be optimized for row rendering.

Each row should include at least:

- inbound order id
- source reference
- external status
- market
- listing title
- listing grade
- customer full name
- original price
- shipping date
- tracking number
- shipper
- tracking status group
- likely arrival bucket
- arrived clicked
- device created
- linked device id
- linked device status if created
- `label_printed` boolean or equivalent derived status field
- last synced at

Do not force the frontend to assemble these from deeply nested raw objects.

Return a clean row DTO.

---

# 24. Frontend Module 01 Scope

## 24.1 Page

The first UI should be an inbound queue page.

It may replace or evolve the current inbound page, but it should now read from your own backend, not directly from BackMarket.

## 24.2 Required UI features

- manual sync button
- table/list of inbound orders
- filters
- visible tracking fields
- Arrived action button
- open linked device if already created
- immediate print-preview flow after Arrived
- print confirmation action after preview
- reprint action from linked device context or action menu

## 24.3 Row actions

For Module 01:

- Arrived
- Open Device (if linked)
- Reprint Label (if linked device exists)

Future:

- refresh single order
- archive/hide
- view raw details

---

# 25. Suggested Frontend Row Columns

Recommended first columns:

- order reference
- customer
- device title
- grade
- offer price
- external status
- shipper
- tracking number
- tracking status group
- likely arrival
- shipping date
- arrived clicked
- linked device
- label status
- actions

This is enough to make the queue operational.

---

# 26. UI Behaviour Rules

## 26.1 Arrived button

Show only when:

- no linked device exists

Disable or hide if:

- `device_created = true`

## 26.2 Open Device button

Show when:

- linked device exists

## 26.3 Print / Reprint controls

### On Arrived success

If label generation succeeds:

- open print preview immediately
- show explicit follow-up action:
  - `Printed, continue`
  - `Skip for now`

### On `Printed, continue`

- call `confirm-printed`
- update device status to `label_printed`
- navigate to device record

### On `Skip for now`

- navigate to device record
- device remains `arrived`
- show `Print Label` action on device page/header/action bar

### If preview generation fails

- show clear warning
- do not lose the created device
- offer `Try Again`
- allow user to open the device anyway

## 26.4 Sync button

Always visible to authorized users.

---

# 27. Tracking in Module 01

Tracking support in Module 01 should be data-model ready, but actual carrier polling can still be deferred slightly if needed.

So Module 01 must:

- store tracking fields
- show tracking data if present
- support queue filtering by tracking fields

But actual Royal Mail/headless update jobs can be implemented as:

- Module 01.5
- or the immediate follow-up slice after basic sync and label flow work

This keeps scope under control.

---

# 28. Error Handling Rules

## 28.1 Sync endpoint must handle

- API auth failure
- network errors
- bad BackMarket response
- pagination issues

Should return:

- clear error summary
- preserve previous sync state if sync fails

## 28.2 Arrived endpoint must prevent

- duplicate device creation
- inbound order not found
- cross-business access
- invalid repeated arrival click

## 28.3 Label render endpoint must handle

- device not found
- cross-business access
- unsupported format
- template errors
- barcode render failure

## 28.4 Confirm printed endpoint must handle

- device not found
- cross-business access
- invalid status transition
- invalid copies count

## 28.5 Important resilience rule

A label problem must never create duplicate devices and must never destroy the successful intake event.

---

# 29. Index Requirements for Module 01

Ensure indexes exist for:

## inbound_orders

- unique: `business_id + source + source_reference`
- `business_id + local_state.device_created`
- `business_id + local_state.hidden_from_inbound`
- `business_id + external_status`
- `business_id + modification_date`
- `business_id + tracking.tracking_number`

## devices

- unique `_id`
- unique `device_id`
- `business_id + inbound_order_id`
- `business_id + status`
- `business_id + label.barcode_value`

## sync_states

- unique `_id`
- `business_id + source`

---

# 30. Manual Test Cases

## 30.1 Sync tests

- trigger manual sync with empty DB
- confirm inbound orders created
- trigger sync again with same data
- confirm no duplicates
- update order in BM / simulate modified payload
- confirm local record updates without losing local state

## 30.2 Arrived tests

- click Arrived on valid inbound row
- confirm device created
- confirm `device_id` generated
- confirm inbound row hidden from active queue
- confirm linked device id stored
- confirm second Arrived click is blocked

## 30.3 Label generation tests

- Arrive with `generate_label = true`
- confirm print preview URL/document returned
- confirm barcode payload equals `device_id`
- confirm label template is `intake_minimal`
- confirm no IMEI/customer data is encoded in barcode

## 30.4 Print confirmation tests

- after preview, click `Printed, continue`
- confirm device status moves from `arrived` to `label_printed`
- confirm `label.print_count = 1`
- confirm `last_printed_at` saved

## 30.5 Skip / failure tests

- Arrive and skip printing
- confirm device still exists
- confirm status remains `arrived`
- confirm reprint action is available

- simulate label rendering failure
- confirm device still exists
- confirm intake not duplicated
- confirm warning shown
- confirm user can re-open label render later

## 30.6 Reprint tests

- reprint existing label
- confirm same `device_id` / barcode value used
- confirm no new device created
- confirm print count increments only after confirmation

## 30.7 Business isolation tests

- try reading another business's inbound records
- try rendering another business's label
- try confirming print on another business's device
- confirm all blocked

---

# 31. Success Criteria

Module 01 is complete when:

- BackMarket buyback orders can be synced into local DB
- active inbound queue works from local DB
- duplicates are prevented
- local workflow state survives repeated syncs
- Arrived action creates a proper device record
- created device gets a global `device_id`
- inbound order is linked to device
- processed inbound item no longer clutters the queue
- an intake barcode label can be generated immediately after Arrived
- barcode payload equals the internal `device_id`
- user can confirm printing and move device to `label_printed`
- user can reprint the same label later

At that point the platform has a proper inbound + barcode intake foundation.

---

# 32. Immediate Follow-Up Module

Once this expanded Module 01 is complete, the next implementation slice should be:

```text
scan-to-open workflow + minimal device detail page hardening
```

That will turn label generation into a full operational scan workflow.

After that:

```text
USB enrichment + diagnostics + CheckMEND decision flow
```

---

# 33. Implementation Notes for Coding Start

If coding starts from this spec, the recommended build order inside Module 01 is:

## Step 1

Create:

- `system_counters` support
- `device_id` generator service

## Step 2

Create:

- inbound sync service
- inbound repository
- queue endpoint

## Step 3

Create:

- minimal devices schema/model
- device repository
- inbound-to-device creation service

## Step 4

Create:

- Arrived endpoint
- create device + link inbound logic

## Step 5

Create:

- label generation service
- barcode render helper
- PDF/HTML template render
- render label endpoint

## Step 6

Create:

- confirm printed endpoint
- controlled status transition `arrived -> label_printed`

## Step 7

Create:

- frontend Arrived action
- print preview modal/tab flow
- confirmation action
- route to device detail page or placeholder device page

This gives the exact workflow you want:

```text
Inbound page
→ click Arrived
→ create device record
→ generate device_id
→ print label
→ open device record
```
