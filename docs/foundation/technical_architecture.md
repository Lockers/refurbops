# RefurbOps Platform — Technical Architecture

This document defines the technical architecture for the RefurbOps platform based on the agreed business blueprint.

It is intended to guide implementation before code is written.

---

# 1. Technology Stack

## Backend
- **Python**
- **FastAPI**
- **Pydantic**
- **MongoDB**
- **PyMongo / Motor**
- **Service + Repository architecture**

## Frontend
- **React**
- **TypeScript**
- **Vite**
- UI library to be chosen later, but should support:
  - data tables
  - forms
  - badges/status tags
  - dashboards
  - drawers/modals

## Database
- **MongoDB**
- Multi-tenant by `business_id`

## File Storage
Initial phase:
- local/dev storage acceptable

Cloud-ready target:
- object storage for:
  - diagnostics PDFs
  - CheckMEND reports
  - images
  - exports
  - generated labels/PDFs if needed

## Hardware / Integrations
- USB barcode scanner as keyboard input
- desktop label printer
- later: local Python USB agent for phone data capture
- later: diagnostics integration bridge
- later: CheckMEND integration
- later: marketplace integrations

---

# 2. Repository Structure

The platform will use a **single repository**.

Recommended structure:

```text
refurbops/
  backend/
  frontend/
  docs/
  scripts/
Why

frontend and backend changes are tightly linked

easier git workflow

shared docs stay with the code

simplest long-term structure at current scale

3. Backend Architecture

Backend should use a clean layered structure.

Recommended structure:

backend/
  app/
    api/
      routers/
    core/
      config.py
      database.py
      security.py
    schemas/
    services/
    repositories/
    integrations/
    models/
    utils/
    main.py
  tests/
  requirements.txt
  .env.example
Responsibilities
api/routers/

HTTP endpoints only.

parse requests

call services

return responses

No real business logic here.

schemas/

Pydantic models for:

request bodies

response bodies

shared DTOs

validation schemas

services/

Business logic and workflow orchestration.
Examples:

intake workflow

device status transitions

donor part assignment

repair routing

profitability calculations

repositories/

Database access only.
Examples:

device repository

inbound order repository

repair repository

inventory repository

integrations/

External systems and adapters.
Examples:

CheckMEND

barcode label generation

printer adapter

Blackbelt/Phonecheck import bridge

USB device reader bridge

marketplace connectors

core/

Shared application concerns.
Examples:

settings

DB connection

auth helpers

tenancy helpers

models/

Optional internal domain models/constants where useful.
Examples:

status enums

note categories

role constants

utils/

Small reusable helpers only.

4. Frontend Architecture

Recommended structure:

frontend/
  src/
    app/
    pages/
    components/
    features/
    hooks/
    services/
    types/
    utils/
    routes/
    main.tsx
Responsibilities
pages/

Top-level screens.
Examples:

inbound page

intake queue

device detail page

repair queue

inventory page

donor devices

VAT reports

components/

Reusable UI components.
Examples:

status badges

barcode scan input

record headers

file attachment panels

note panels

action bars

features/

Feature-specific UI logic grouped by module.
Examples:

intake

repairs

inventory

donor devices

accounting

services/

Frontend API clients.
Examples:

device API

inbound API

repair API

inventory API

types/

Shared TypeScript interfaces/types aligned to backend responses.

routes/

Route definitions and protected route logic.

5. Multi-Tenant Model

The system is multi-business from day one.

Core Rule

All business-owned records must include:

business_id

Examples:

devices

inbound orders

repairs

parts orders

listings

accounting records

notes

attachments metadata

Tenant Safety Rule

All business-facing queries must filter by:

business_id

The platform owner role is the only exception and should use controlled access patterns.

6. Core Collections

Recommended Mongo collections for v1/v1.5:

businesses
users
inbound_orders
devices
device_notes
device_attachments
repair_jobs
parts_orders
donor_parts
inventory_items
sales
returns
vat_margin_entries
system_counters

Later additions may include:

marketplace_listings

pricing_rules

price_history

diagnostics_imports

webhook_events

subscriptions

7. Main Data Relationships
7.1 Businesses

Each business owns:

users

inbound orders

devices

inventory

repairs

accounting records

7.2 Inbound Order → Device

Structure:

Inbound Order
   ↓
Device

Most BackMarket flows will be:

one inbound order

one device

But architecture must support:

one inbound order

multiple devices

7.3 Device as Primary Workflow Object

The device is the main operational object.

Everything attaches to the device:

USB data

diagnostics

repair history

donor status

attachments

sale

return

warranty events

8. Device Record Design

The device document should be the central lifecycle record.

Suggested high-level shape:

{
  "device_id": "DEV-00000001",
  "business_id": "biz_001",
  "inbound_order_id": "inb_001",
  "status": "arrived",
  "flags": [],
  "source": {
    "type": "backmarket_tradein",
    "reference": "BM-12345"
  },
  "customer": {
    "name": "John Smith",
    "address": "10 High Street"
  },
  "expected_device": {
    "make": "Apple",
    "model": "iPhone 14",
    "condition": "Good",
    "buy_price": 210.0
  },
  "usb_data": {},
  "diagnostics": {},
  "repair_summary": {},
  "inventory_summary": {},
  "sale_summary": {},
  "return_summary": {},
  "notes_count": 0,
  "attachments_count": 0,
  "created_at": "",
  "updated_at": ""
}

This should be expanded carefully during schema design.

9. Device ID Generation

Device IDs must be globally unique across the platform.

Format:

DEV-00000001
Generation Strategy

Use a dedicated Mongo collection:

system_counters

Example record:

{
  "_id": "device_id",
  "next_value": 124
}

When generating a new ID:

atomically increment counter

format padded value

return device ID

This is better than UUIDs because:

easier for barcode labels

easier for humans

easier for phone-based workflows

10. Status Model

Use a full lifecycle status model with controlled transitions.

Statuses

Initial suggested statuses:

expected
arrived
label_printed
usb_data_captured
diagnostics_complete
awaiting_checkmend
awaiting_counter_offer_response
accepted_for_processing
repair_queue
awaiting_parts
awaiting_third_party_repair
inventory_ready
trade_in_route
donor_device
returned_to_customer
listed
sold
returned
closed
Flags / Secondary Indicators

Use separate flags for cross-cutting states, for example:

repair_required
checkmend_failed
parts_ordered
overdue
warranty_return
activation_lock_detected
Rule

Primary status = current lifecycle stage
Flags = important extra conditions

11. Notes Model

Internal notes should be structured and stored separately or as embedded subdocuments depending on scale.

Recommended v1 approach:

separate collection for easier querying/audit

Example collection:

device_notes

Suggested fields:

business_id

device_id

note_type

content

created_by

created_at

12. Attachments Model

Attachments should be metadata-driven.

Recommended collection:

device_attachments

Suggested fields:

business_id

device_id

attachment_type

storage_path

original_filename

uploaded_by

uploaded_at

is_required_for_sale

Attachment types may include:

diagnostics_report

checkmend_report

customer_photo

repair_photo

sale_condition_photo

13. Repairs Architecture

Repairs should not just be a loose field on the device.

Recommended structure:

repair_jobs collection

Each repair job should support:

device linkage

internal or third-party repair

status

parts ordered

parts used

outcome

cost

This gives proper traceability and supports multiple repair events on one device over time.

14. Donor Devices and Harvested Parts

Donor devices remain devices.

Do not convert them into anonymous loose stock immediately.

Use:

device status = donor_device

harvested parts tracked separately

Recommended collection:

donor_parts

Suggested fields:

business_id

donor_device_id

part_type

condition

status (available, reserved, used, discarded)

internal_value

used_in_device_id

removed_at

15. Inventory Architecture

Inventory is asset-level.

Each device becomes an inventory item when ready for sale.

Recommended collection:

inventory_items

This should reference:

device_id

sale grade

battery health

route to market

availability status

One device = one inventory item.

16. Sales Architecture

Sales should be recorded separately from inventory.

Recommended collection:

sales

Fields should include:

business_id

device_id

inventory_item_id

sales_channel

order_reference

customer_name

customer_address

sale_price

marketplace_fee_data

sold_at

This supports:

VAT margin entries

profitability

returns

channel reporting

17. Returns Architecture

Returned devices reopen the same device record.

But the return event itself should also be stored explicitly.

Recommended collection:

returns

Return record includes:

device linkage

return type

reason

diagnostics

work done

resolution

timestamps

This preserves full lifecycle history.

18. VAT / Accounting Architecture

Recommended collection:

vat_margin_entries

This should support:

purchase side

sale side

margin calculation

PDF generation metadata

VAT period linkage

Each business should have its own VAT settings:

VAT registration status

VAT scheme

quarter boundaries / periods

This belongs at business configuration level.

19. Authentication and Authorization

Initial recommendation:

simple JWT-based auth for API

role-based authorization checks in backend

Roles:

platform_owner

business_admin

technician

viewer

The backend must enforce permissions, not just frontend hiding.

20. Search Model

Search should be scoped to business.

Supported search types later:

device_id

IMEI

serial

inbound reference

order reference

IMEI search must be business-scoped only.

21. Printer and Barcode Architecture
Barcode Scanner

Use USB barcode scanner in keyboard mode.

Frontend behaviour:

scan into focused input

lookup by device_id

open matching record

No special browser hardware API required for v1.

Label Printer

Printing should be handled through a dedicated backend label-generation flow.

Recommended concept:

backend generates printable label payload

frontend triggers print action

exact printer integration can initially be browser/system based

later: local print bridge if required

Barcode value should only contain:

device_id
22. USB Device Data Architecture

Do not tightly couple the main backend to a specific USB tool at first.

Recommended architecture:

main web app remains cloud/local web system

later add optional local Python agent

local agent reads connected phone data

agent posts structured payload to backend

Why:

cloud-ready architecture

local hardware support

easier future diagnostics bridges

23. Diagnostics Integration Architecture

Blackbelt360 / Phonecheck should initially be treated as external systems.

V1 approach:

attach reports manually

optionally store parsed summary fields

Later:

import bridge / parser

direct integration if available

This avoids overcommitting to a vendor-specific implementation too early.

24. CheckMEND Architecture

V1 approach:

store CheckMEND results and report reference

allow attachment of report

use result in workflow gating

Later:

direct API integration if commercially justified

CheckMEND should be a required step before sale listing.

25. Marketplace Architecture

Marketplace support should be layered.

Core Rule

Inventory item is channel-agnostic.

Later Listing Layer

Separate listing records per marketplace.

Possible later collection:

marketplace_listings

This should support:

inventory item linkage

channel

suggested price

actual listing price

listing status

external listing ID

This avoids polluting the core inventory record.

26. Pricing Architecture

The pricer should be implemented as a dedicated module later, not baked randomly into inventory logic.

High-level future module areas:

cost basis inputs

competitor pricing inputs

marketplace fee models

recommended price output

predicted profit output

The rest of the system should consume pricing outputs, not own pricer logic everywhere.

27. Dashboard / Queue Architecture

Queues should be generated from:

primary status

flags

age/time thresholds

Not manual lists.

Examples:

awaiting diagnostics

awaiting parts

overdue third-party repairs

ready for sale

awaiting counter-offer response

This is a strong fit for backend-generated filtered endpoints.

28. Deployment Model
Development

local backend

local frontend

local or cloud Mongo depending on phase

local scanner/printer support

Production-ready direction

cloud-hosted backend

cloud-hosted frontend

MongoDB Atlas

object storage for files

optional local hardware agent at each business

This supports:

phone access

multi-device access

multi-business SaaS

local shop hardware integrations

29. Environment and Config

Backend should use environment-based config for:

DB connection

auth secret

file storage mode

app URLs

feature toggles

future external integrations

Use:

.env for local

.env.example committed

secrets never committed

Frontend should also use environment config for:

API base URL

feature flags where needed

30. First Implementation Slice

The first build slice should be:

Inbound page
→ click Arrived
→ generate device_id
→ print barcode label
→ open device record

Why this first:

high operational value

low implementation risk

unlocks the rest of the workflow

builds directly on your existing inbound page

This should be implemented before USB automation, diagnostics parsing, or marketplace logic.