# RefurbOps Platform — BackMarket Inbound Sync Spec v2

This document defines how BackMarket buyback orders are synchronised, tracked, and processed within the RefurbOps platform.

Version 2 expands the original inbound sync design to include **carrier tracking and arrival prediction**, allowing businesses to better anticipate when devices will physically arrive.

---

# 1. Purpose

BackMarket buyback orders are a primary source of inbound devices.

The platform must:

- synchronise buyback orders from BackMarket
- store them locally
- prevent duplicates
- preserve local workflow state
- track shipment progress
- predict likely arrival windows
- convert inbound orders into device lifecycle records

BackMarket is the **external source of order data**.

RefurbOps is the **source of truth for operational workflow**.

---

# 2. BackMarket Endpoints

## 2.1 List buyback orders


GET /ws/buyback/v1/orders


Returns paginated buyback orders.

Supports filtering by:

- `creationDate`
- `modificationDate`
- `paymentDate`
- `receivedDate`
- `shippingDate`
- `suspendedDate`
- `status`
- `productId`
- `page`

---

## 2.2 Retrieve single order


GET /ws/buyback/v1/orders/{buybackOrderId}


Used for:

- manual refresh
- debugging
- recovering a specific order

---

# 3. Unique Identifier

The external identifier is:


orderPublicId


Inbound records must store:


source = backmarket_buyback
source_reference = orderPublicId


Unique index rule:


business_id + source + source_reference


---

# 4. Sync Strategy

## Incremental Sync

Orders should be synchronised using:


modificationDate


This captures:

- new orders
- shipping updates
- counter-offers
- payment updates
- status changes

---

## Incremental Sync Flow


last_successful_sync_at
↓
subtract overlap window
↓
GET orders with modificationDate >= effective_sync_from
↓
page through results
↓
UPSERT into inbound_orders
↓
update sync state


---

## Sync Overlap Window

Recommended overlap:


24 hours


This prevents missing records due to delayed API updates or timezone differences.

---

# 5. Sync Modes

Three supported sync modes:

## Automatic Sync

Scheduled incremental sync.

Recommended schedule:


Every 2 hours


---

## Manual Refresh

User-triggered incremental sync from the UI.

Purpose:

- immediate queue refresh
- operational control

---

## Full Resync

Admin-only operation.

Used for:

- rebuilding inbound data
- fixing sync corruption
- debugging

---

# 6. Sync State Storage

Collection:


sync_states


Example:

```json
{
  "_id": "sync_backmarket_buyback_biz_001",
  "business_id": "biz_001",
  "source": "backmarket_buyback",
  "last_successful_sync_at": "2026-03-07T10:00:00Z",
  "last_attempted_sync_at": "2026-03-07T10:01:00Z",
  "last_full_resync_at": null,
  "last_error": null
}
7. Inbound Orders Collection

Collection:

inbound_orders

Stores both:

external BackMarket data

internal workflow state

8. Example Inbound Order Structure
{
  "business_id": "biz_001",
  "source": "backmarket_buyback",
  "source_reference": "US-24527-ABCDE",

  "external_status": "TO_SEND",
  "market": "FR",

  "creation_date": "2019-03-21T14:28:30+01:00",
  "modification_date": "2019-03-26T08:00:53+01:00",

  "shipping_date": "2019-03-21T14:37:54+01:00",
  "receival_date": null,
  "payment_date": null,

  "listing": {
    "sku": "21000021",
    "product_id": 2311,
    "title": "Apple iPhone XS 64 Go",
    "grade": "DIAMOND"
  },

  "customer": {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+33699887766"
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

  "local_state": {
    "arrived_clicked": false,
    "device_created": false,
    "linked_device_id": null,
    "hidden_from_inbound": false
  }
}
9. Local Workflow Overlay

BackMarket status is external.

Local workflow must use separate fields.

Example:

external_status → marketplace state
local_state → business workflow state

Local state fields:

arrived_clicked

device_created

linked_device_id

hidden_from_inbound

10. Inbound Queue Logic

Inbound queue should display records where:

device_created = false
AND hidden_from_inbound = false

This prevents processed orders from reappearing.

11. Shipment Tracking Layer

Only approximately 50% of trade-in orders are actually shipped by customers.

Tracking should therefore activate only once a tracking number exists.

Example condition:

tracking_number != null
12. Tracking Status Model

Carrier tracking responses should be normalised into internal statuses.

Fields:

tracking.status_raw
tracking.status_group
tracking.last_checked_at
tracking.last_event_at
tracking.likely_arrival_bucket
13. Status Group Mapping

Example mapping:

Carrier message	Internal status
Label created	tracking_created
Accepted by carrier	accepted_by_carrier
In transit	in_transit
At mail centre	at_mail_centre
Out for delivery	out_for_delivery
Delivered	delivered
14. Arrival Prediction Buckets

Use simple prediction buckets for operations.

not_shipped
in_transit
likely_arriving_soon
out_for_delivery
delivered

Example mapping:

Tracking status	Bucket
at_mail_centre	likely_arriving_soon
out_for_delivery	today
accepted_by_carrier	in_transit
15. Royal Mail / Carrier Tracking

Tracking logic should be abstracted via a carrier adapter layer.

Example design:

CarrierTrackingService
    ↓
RoyalMailAdapter
DHLAdapter
DPDAdapter

This allows future support for multiple carriers.

16. Tracking Update Strategy

Tracking updates should run only on shipped orders.

Example job:

every 4 hours
↓
find inbound orders with tracking_number
↓
check tracking status
↓
update tracking fields

Manual refresh should also be available.

17. Arrival Workflow

When a shipment physically arrives:

User clicks:

Arrived

Then:

mark inbound order arrived

create device record

generate device_id

print barcode

link inbound order → device

Update inbound record:

device_created = true
linked_device_id = DEV-xxxxx
hidden_from_inbound = true
18. Device Creation Mapping

Fields copied to device:

source

source_reference

customer snapshot

listing title

grade

offer price

market

Initial device values:

status = arrived
route = unknown
19. Raw Payload Storage

Each inbound record should also store:

raw_payload

This preserves the full API response.

Useful for:

debugging

API changes

future feature expansion

20. Index Recommendations

Indexes for inbound_orders:

business_id + source + source_reference (unique)
business_id + external_status
business_id + local_state.device_created
business_id + tracking.tracking_number
business_id + modification_date
21. First Implementation Scope

BackMarket inbound v1 must support:

manual sync

incremental sync by modificationDate

pagination

deduplication

inbound queue

arrival workflow

device creation

barcode linking

shipment tracking layer

likely arrival buckets

22. Operational Outcome

Once implemented:

BackMarket sync
↓
Inbound queue shows only relevant items
↓
Tracking predicts arrival
↓
Device arrives
↓
User clicks Arrived
↓
Device record created
↓
Barcode printed
↓
Device lifecycle begins