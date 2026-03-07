# RefurbOps Platform — Status Model v1

This document defines the lifecycle statuses, flags, and allowed transitions for devices in the RefurbOps platform.

The goal is to keep workflow logic clear, consistent, and enforceable in the backend.

---

# 1. Status Model Principles

## 1.1 Primary Status
Each device has **one primary status**.

The primary status answers:

> Where is this device right now in its lifecycle?

Examples:
- `arrived`
- `awaiting_diagnostics`
- `repair_queue`
- `inventory_ready`
- `sold`

---

## 1.2 Flags
Each device may also have **zero or more flags**.

Flags answer:

> What important conditions apply to this device right now?

Examples:
- `repair_required`
- `checkmend_failed`
- `parts_ordered`
- `overdue`
- `warranty_return`

Flags do **not** replace status.

---

## 1.3 Route / Disposition
Each device also has a **route** field.

The route answers:

> What is the intended commercial path for this device?

Examples:
- `sale`
- `trade_in`
- `donor`
- `return_to_customer`

So:

- **status** = current workflow stage
- **flags** = important conditions
- **route** = intended commercial outcome

---

# 2. Primary Status List

## Intake / early lifecycle

```text
expected
arrived
label_printed
usb_data_captured
awaiting_diagnostics
diagnostics_complete
awaiting_checkmend
awaiting_counter_offer_response
accepted_for_processing
Repair / routing lifecycle
repair_queue
awaiting_parts
awaiting_third_party_repair
repair_in_progress
repair_complete
inventory_ready
trade_in_route
donor_device
returned_to_customer
Sales lifecycle
listed
sold
Return / after-sale lifecycle
returned
closed
3. Status Definitions
expected

The inbound order exists, but the physical device has not yet arrived.

arrived

The physical device has arrived and has been booked in.

label_printed

A barcode label has been generated and printed for the device.

usb_data_captured

The device has been connected and USB/device data has been pulled.

awaiting_diagnostics

The device is waiting for Blackbelt / Phonecheck diagnostics.

diagnostics_complete

Diagnostics have been completed and results recorded.

awaiting_checkmend

The device passed the required stage to proceed to CheckMEND checking.

awaiting_counter_offer_response

A counter-offer has been issued and the business is waiting for the customer response.

accepted_for_processing

The device has been accepted for continued workflow after diagnostics / counter-offer acceptance.

repair_queue

The device has been accepted and is waiting for internal repair work.

awaiting_parts

The device is waiting for one or more ordered parts to arrive.

awaiting_third_party_repair

The device has been sent to an external repair provider and is awaiting return.

repair_in_progress

Repair work is currently being carried out internally.

repair_complete

Repair work has been completed and the device is ready for next evaluation.

inventory_ready

The device is ready to become or already has become active stock for sale.

trade_in_route

The device is being routed to a trade-in resale channel rather than normal sale stock.

donor_device

The device is retained as a donor / parts harvesting device.

returned_to_customer

The device has been rejected or declined and is being returned to the customer.

listed

The device has been listed on one or more sales channels.

sold

The device has been sold.

returned

The device has come back after sale (warranty or out-of-warranty return).

closed

The lifecycle is complete and no active operational work remains.

4. Route Values

Allowed route values:

sale
trade_in
donor
return_to_customer
unknown
Meaning
sale

Device intended for direct sale through inventory/marketplaces.

trade_in

Device intended for trade-in resale route.

donor

Device intended to remain as a donor / parts source.

return_to_customer

Device intended to be returned to the original customer/source.

unknown

Commercial route not yet decided.

5. Flag List

Initial supported flags:

repair_required
checkmend_failed
parts_ordered
overdue
warranty_return
out_of_warranty_return
activation_lock_detected
jailbreak_detected
diagnostics_failed
counter_offer_required
ready_for_sale
third_party_repair
manual_review_required
6. Flag Definitions
repair_required

Device requires repair before final routing/sale.

checkmend_failed

CheckMEND has produced a blocking result.

parts_ordered

At least one required part has been ordered.

overdue

Device is overdue for the current stage.

warranty_return

Returned under warranty.

out_of_warranty_return

Returned outside warranty.

activation_lock_detected

Activation lock detected on device.

jailbreak_detected

Device appears jailbroken.

diagnostics_failed

Diagnostics found issues that affect normal pass flow.

counter_offer_required

A counter-offer is required based on findings.

ready_for_sale

All required gating conditions for sale are satisfied.

third_party_repair

Device currently involves external repair workflow.

manual_review_required

A human review is needed due to mismatch/risk/exception.

7. Allowed Status Transitions

This defines the normal permitted movements.

7.1 Intake flow
expected
  → arrived

arrived
  → label_printed
  → usb_data_captured
  → awaiting_diagnostics

label_printed
  → usb_data_captured
  → awaiting_diagnostics

usb_data_captured
  → awaiting_diagnostics
  → diagnostics_complete

awaiting_diagnostics
  → diagnostics_complete
7.2 Post-diagnostics flow
diagnostics_complete
  → awaiting_checkmend
  → awaiting_counter_offer_response
  → repair_queue
  → donor_device
  → returned_to_customer

Notes:

if diagnostics pass normally, route to awaiting_checkmend

if diagnostics fail with counter-offer required, route to awaiting_counter_offer_response

if immediately identified as donor, route to donor_device

if rejected/returning, route to returned_to_customer

7.3 Counter-offer flow
awaiting_counter_offer_response
  → accepted_for_processing
  → returned_to_customer
  → closed

Notes:

accepted counter-offer = accepted_for_processing

declined counter-offer = returned_to_customer

unresolved/closed case = closed if business policy finalises it that way

7.4 CheckMEND flow
awaiting_checkmend
  → accepted_for_processing
  → returned_to_customer

Notes:

clear result = accepted_for_processing

blocked/finance/blacklist issue = returned_to_customer

7.5 Accepted processing flow
accepted_for_processing
  → repair_queue
  → inventory_ready
  → trade_in_route
  → donor_device

Notes:

no repair needed and for sale = inventory_ready

repair needed = repair_queue

route to trade-in = trade_in_route

donor decision = donor_device

7.6 Internal repair flow
repair_queue
  → awaiting_parts
  → repair_in_progress
  → awaiting_third_party_repair
  → donor_device

awaiting_parts
  → repair_in_progress
  → donor_device

repair_in_progress
  → repair_complete
  → awaiting_parts
  → awaiting_third_party_repair
  → donor_device

repair_complete
  → inventory_ready
  → trade_in_route
  → donor_device
7.7 Third-party repair flow
awaiting_third_party_repair
  → repair_complete
  → repair_queue
  → donor_device

Notes:

returned repaired = repair_complete

returned for further internal work = repair_queue

found uneconomical = donor_device

7.8 Inventory / sales flow
inventory_ready
  → listed
  → trade_in_route
  → donor_device

trade_in_route
  → sold
  → closed

listed
  → sold
  → inventory_ready
  → closed

Notes:

listed → inventory_ready covers delisting back to stock

trade_in_route → sold means completed external trade-in resale

trade_in_route → closed if business wants to close that path once externally processed

7.9 After sale / return flow
sold
  → returned
  → closed

returned
  → repair_queue
  → repair_in_progress
  → inventory_ready
  → returned_to_customer
  → closed

Notes:

returned devices reopen the same device record

returned devices may go through repair and re-sale workflows again if business process allows it

7.10 End states

Typical end states:

closed
returned_to_customer
donor_device
sold

But only closed is the true workflow-final status.

8. Invalid Transition Examples

These should be blocked by the backend.

expected → sold
arrived → sold
diagnostics_complete → sold
awaiting_parts → listed
donor_device → listed
returned_to_customer → listed

These are invalid because they bypass required workflow stages.

9. Suggested Status-to-Flag Rules

These are recommended automatic flag behaviours.

Examples
If diagnostics fail

Add:

diagnostics_failed
repair_required
If counter-offer required

Add:

counter_offer_required
If CheckMEND fails

Add:

checkmend_failed
manual_review_required
If parts order exists and still open

Add:

parts_ordered
If returned under warranty

Add:

warranty_return
If device is sale-gated complete

Add:

ready_for_sale
10. Overdue Logic

The overdue flag should be applied by business rules based on elapsed time.

Examples:

awaiting_counter_offer_response > configured threshold

awaiting_parts > configured threshold

awaiting_third_party_repair > configured threshold

repair_queue with no activity > configured threshold

This should support dashboard reminders and colour-coding.

11. Sale Gating Rules

A device should only become effectively sale-ready when required conditions are met.

Suggested required conditions:

diagnostics complete

diagnostics report attached

CheckMEND complete

CheckMEND not failed

final grade set

route = sale or valid route for chosen channel

When all are true:

set sale_readiness.ready_for_sale = true

optionally add ready_for_sale flag

12. UI Use of Statuses

The UI should use statuses for:

badges on rows/cards

filters/dropdowns

dashboard queues

action enable/disable logic

Examples:

only show "Run CheckMEND" action when status = awaiting_checkmend

only show "Print Label" when status = arrived and not already printed

only show "List for Sale" when status = inventory_ready and sale gating is satisfied

13. Colour Coding Recommendation

Suggested colour usage in UI:

expected / passive          = grey
active work needed          = blue
awaiting external response  = yellow
ready states                = green
problem / blocked           = red
donor / non-standard route  = purple or orange

Example mapping:

awaiting_diagnostics → blue

awaiting_parts → yellow

inventory_ready → green

checkmend_failed flag → red

donor_device → purple

These are UI suggestions only, not backend rules.

14. v1 Implementation Rule

For v1, enforce transitions in the backend service layer.

Recommended pattern:

keep allowed transitions in one central status-transition map

all status changes must go through a workflow/status service

routers should never directly set arbitrary statuses

This prevents lifecycle corruption.

15. Future Extension Notes

Later versions may add:

full status history collection

workflow event log

automated transition triggers

SLA/reminder rules per business

per-business configurable workflow variants

But v1 should keep:

one primary status

flags

route

controlled transitions