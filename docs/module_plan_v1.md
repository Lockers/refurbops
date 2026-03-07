# RefurbOps Platform — Module Plan v1

This document defines the initial build order for the RefurbOps platform.

The goal is to turn the agreed blueprint, technical architecture, data model, and status model into a practical implementation sequence.

The platform should be built in **vertical slices**, not as disconnected technical layers.

Each module should deliver usable business value before the next one begins.

---

# 1. Build Principles

## 1.1 Build in vertical slices
Each module should include:

- business rules
- backend models/schemas
- backend services
- backend endpoints
- frontend UI
- manual testing flow

Do not build backend-only or frontend-only in isolation unless necessary.

---

## 1.2 Highest value first
Start with features that:

- improve the real workflow immediately
- reduce manual handling
- create the foundation for later modules

---

## 1.3 Reuse current working flow
The existing inbound page and inbound workflow are already useful.

The first implementation should build on that, not replace it unnecessarily.

---

## 1.4 Avoid over-automation early
V1 should support the correct workflow first.

Automation can be added later once the workflow is stable.

---

# 2. v1 Module Order

Recommended implementation order:

```text
1. Intake Foundation Module
2. Barcode and Label Module
3. Device Detail Module
4. Diagnostics and Attachments Module
5. CheckMEND and Decision Module
6. Repair and Parts Module
7. Donor Device Module
8. Inventory Ready Module
9. Sales and Sale Record Module
10. Returns and Warranty Module
11. VAT Margin and Accounting Foundation Module

This is the recommended order because each module depends on the previous ones.

3. Module 1 — Intake Foundation
Goal

Extend the current inbound page so that it becomes the operational entry point for device lifecycle handling.

Business outcome

When a device arrives, staff can:

click Arrived

create a device record from the inbound order

generate a device ID

move the device into the intake workflow

Scope
Backend

inbound_orders read support

devices creation service

device ID generation service

status initialisation

route initialisation

customer snapshot copy

expected device snapshot copy

Frontend

use existing inbound page

add Arrived action

show whether a device record has already been created

route to device record after creation

Device creation behaviour

On Arrived:

Inbound Order
→ Create Device
→ Assign device_id
→ Status = arrived
→ Route = unknown or sale default
Deliverable

A working inbound page where physical arrivals become real tracked device records.

Why first

This is the foundation of the whole system.

Nothing else should be built before device creation is stable.

4. Module 2 — Barcode and Label Module
Goal

Give every arrived device a scannable barcode identity.

Business outcome

When a device is booked in:

a barcode label can be printed

the label is attached to the device bag/tray

scanning the barcode opens the device record

Scope
Backend

label generation endpoint

barcode payload generation

print metadata tracking

update status to label_printed if needed

Frontend

print label action on inbound/device page

barcode scan input

open device by device_id

Hardware assumptions

scanner works as keyboard input

label printer printing may initially be browser/system driven

exact printer bridge can come later

Deliverable

Device label printing and scanning workflow works end-to-end.

Why second

The barcode becomes the operational identity for every future module.

5. Module 3 — Device Detail Module
Goal

Create the main device page that becomes the operational control centre for each phone.

Business outcome

Staff can open a device and see:

identity

status

route

customer snapshot

expected device info

location

assigned user

notes and attachments summary

key workflow actions

Scope
Backend

device detail endpoint

device summary response shape

status/route update service

location update support

assignment update support

Frontend

device detail page

status badge

route display

actions bar

summary cards

activity summary panels

Key UI sections

Suggested sections:

header / status

customer + source

expected device

USB data summary

diagnostics summary

CheckMEND summary

financial snapshot

notes

attachments

next actions

Deliverable

A usable device record page that can act as the core operational screen.

Why third

Before adding diagnostics, repairs, and CheckMEND, you need a proper home screen for the device.

6. Module 4 — Diagnostics and Attachments Module
Goal

Support diagnostics workflow and mandatory report handling.

Business outcome

Staff can:

mark diagnostics run

record diagnostics result

upload diagnostics report PDF

store parsed diagnostics summary

move device through diagnostics statuses

Scope
Backend

diagnostics summary update service

attachment upload metadata

diagnostics report attachment type support

status updates:

awaiting_diagnostics

diagnostics_complete

Frontend

diagnostics panel on device detail page

upload diagnostics report

diagnostics result controls

show diagnostics status and date

v1 integration approach

Manual entry / attachment first.

No direct Blackbelt/Phonecheck integration required yet.

Deliverable

Diagnostics stage is recorded properly and sale-gating starts to become possible.

Why fourth

This is the first real enrichment step after booking in.

7. Module 5 — CheckMEND and Decision Module
Goal

Add device history checking and route decision handling.

Business outcome

Staff can:

record CheckMEND result

attach/store report details

see blocking flags

move device into:

accepted for processing

return to customer

counter-offer path

Scope
Backend

CheckMEND summary update

CheckMEND attachment support

decision actions

status/flag updates:

awaiting_checkmend

awaiting_counter_offer_response

accepted_for_processing

returned_to_customer

Frontend

CheckMEND panel

result entry controls

report reference / upload area

decision action buttons

decision warnings

Deliverable

A complete post-diagnostics decision stage.

Why fifth

Once diagnostics are done, this is the key business gate before devices continue.

8. Module 6 — Repair and Parts Module
Goal

Track repairs and ordered parts against devices.

Business outcome

Staff can:

create repair jobs

mark internal or third-party repair

order parts

track parts arrival

record repair costs

move device through repair statuses

Scope
Backend

repair_jobs collection

parts_orders collection

repair job services

parts order services

status transitions:

repair_queue

awaiting_parts

repair_in_progress

awaiting_third_party_repair

repair_complete

Frontend

repair jobs section

parts orders section

parts status display

third-party repair details

repair cost summary

Deliverable

A real repair workflow with financial traceability.

Why sixth

Repair tracking is a core selling point and essential for cost/profit later.

9. Module 7 — Donor Device Module
Goal

Support donor phones and harvested parts tracking.

Business outcome

Staff can:

mark device as donor

define known good/known bad parts

create harvested donor part records

assign donor parts into repairs

track internal donor part value

Scope
Backend

donor route handling

donor_parts collection

donor part creation/update/use flow

donor-to-repair linkage

Frontend

donor status display

donor parts list

mark parts available/unavailable

assign donor part to another device

Deliverable

A working donor phone/parts harvesting system.

Why seventh

This depends on stable repair logic and device routing.

10. Module 8 — Inventory Ready Module
Goal

Move accepted devices into sale-ready stock.

Business outcome

Staff can:

set final grade

confirm sale readiness

create inventory item

view inventory-ready devices

Scope
Backend

inventory_items creation

final grade support

sale readiness logic

inventory summary snapshot updates

Frontend

final grading controls

inventory readiness checklist

ready-for-sale queue

Deliverable

Devices can become real stock items with clean readiness rules.

Why eighth

Only once repair, diagnostics, and decision logic are stable.

11. Module 9 — Sales and Sale Record Module
Goal

Record completed sales and support channel-aware sale data.

Business outcome

Staff can:

record device sale

store sales channel

store customer name/address

store order reference

calculate actual profit snapshot

Scope
Backend

sales collection

sale record service

device status transition to sold

update financial snapshot with actual sale data

Frontend

sale record form

sold device detail section

sales summary data

Deliverable

Proper sale records linked to the device lifecycle.

Why ninth

You need inventory first before sales handling.

12. Module 10 — Returns and Warranty Module
Goal

Allow sold devices to be reopened and tracked through returns/warranty workflows.

Business outcome

Staff can:

reopen device record

create return event

mark warranty or out-of-warranty

record findings and outcome

route returned device back into repair or closure

Scope
Backend

returns collection

return creation service

device reopen logic

return-linked status changes

Frontend

create return action

return event panel

warranty/out-of-warranty display

Deliverable

A device can be sold, returned, and processed again without losing its lifecycle history.

Why tenth

Depends on sales data existing first.

13. Module 11 — VAT Margin and Accounting Foundation
Goal

Create the accounting base needed for VAT margin records and future reporting.

Business outcome

The platform starts supporting:

purchase record recall

sale record linkage

VAT margin entries

quarterly VAT basis per business

Scope
Backend

vat_margin_entries collection

VAT settings on business

margin calculation service

accounting snapshot support

Frontend

VAT entry view

business VAT settings

export-ready reporting screens later

Deliverable

Operational data is now connected to accounting output.

Why eleventh

The accounting foundation should be built on top of stable purchase/sale workflow data.

14. Non-Core Modules to Delay

These should not be part of the first implementation cycle.

Delay until later

full marketplace auto-listing

direct Blackbelt/Phonecheck integration

direct CheckMEND API integration

full pricing engine integration

supplier scraping / parts comparison engine

external API for customers/businesses

subscription billing

advanced reporting dashboards

mobile app

These are valuable, but they should not block the core workflow.

15. First Concrete Build Slice

The very first implementation slice should be:

Inbound page
→ click Arrived
→ create device record
→ generate device_id
→ print label
→ open device record
Included pieces

backend device creation service

Mongo counter for device IDs

minimal device document

frontend Arrived action

barcode label generation

device detail route

This is the correct first implementation because it creates the foundation for every next step.

16. Recommended Backend Build Order Inside Module 1

For Module 1 specifically:

Step 1

Create:

system_counters support

device ID generator service

Step 2

Create:

minimal devices schema/model

device repository

Step 3

Create:

inbound-to-device creation service

Step 4

Create:

Arrived endpoint

Step 5

Create:

frontend Arrived action on inbound page

Step 6

Create:

redirect/open device detail page

17. Recommended Frontend Page Order

Initial page order:

existing inbound page (enhance)

device detail page

diagnostics/decision sections on device page

repair queue page

inventory page

donor devices page

sales page

returns page

VAT/accounting pages

18. Success Criteria for v1 Foundation

The platform foundation is considered successful when a business can:

import or create inbound records

mark a device arrived

generate and print barcode

track the device by barcode

record diagnostics

record CheckMEND

decide route

track repairs and parts

move to inventory

record sale

reopen on return

generate core accounting records

At that point the system becomes genuinely usable as a refurb operations platform.

19. Next Implementation Document

Before coding starts, the next optional but useful document is:

module_01_intake_spec.md

This would define the exact v1 feature in detail:

backend endpoints

request/response schemas

frontend UI actions

Mongo document changes

manual test cases

That is the document that would let us start implementation properly.