# RefurbOps Platform — System Blueprint

This document defines the high-level architecture and operational workflow for the RefurbOps platform.  
It represents the agreed system blueprint before implementation begins.

---

# 1. Platform Vision

RefurbOps is a **multi-business refurb operations platform** designed for refurb and repair businesses.

The platform will support the full lifecycle of mobile devices including:

- intake and booking
- barcode tracking
- diagnostics and testing
- repairs
- parts ordering
- donor device management
- inventory
- marketplace sales
- VAT margin accounting
- warranty returns
- profitability tracking

The system must be designed for **multi-tenant SaaS usage**, while also being practical for daily use by the platform owner’s refurb business.

---

# 2. Multi-Business Architecture

The platform will support multiple businesses using the system.

Each business will have isolated data and users.

Structure:


Platform
↓
Business
↓
Users
↓
Devices


Each device record must include:


business_id


This ensures tenant isolation.

---

# 3. User Roles

The system supports four user roles.

## Platform Owner (Super Admin)

Platform-level controller responsible for:

- creating businesses
- managing platform configuration
- managing subscriptions
- performing system support

The platform owner should **not casually access sensitive tenant data**.

---

## Business Admin

Responsible for managing a business account.

Permissions:

- manage users
- manage integrations and API keys
- configure pricing logic
- override workflows
- access all business data

---

## Technician

Operational user responsible for device handling.

Permissions include:

- booking in devices
- attaching labels
- running diagnostics
- updating repair jobs
- managing donor devices
- updating device lifecycle status

---

## Viewer

Read-only role.

Permissions include:

- scanning devices
- viewing device information
- searching device records

No operational changes allowed.

---

# 4. Order and Device Model

Inbound items are modelled as:


Inbound Order
↓
Device


Example:


BackMarket Order BM-12345
↓
Device DEV-000123


Each device receives its own lifecycle.

The order acts as contextual metadata (customer, source, shipping).

The **device record is the primary workflow object**.

---

# 5. Device Identity

Each device receives a **globally unique device ID**.

Example format:


DEV-00000001
DEV-00000002


This ID is used for:

- barcode labels
- workflow tracking
- repairs
- sales
- warranty returns

The device ID must remain constant for the entire lifecycle.

---

# 6. Barcode Workflow

When a device arrives:

1. Staff clicks **Arrived**
2. System generates **device_id**
3. Barcode label printed
4. Label attached to device bag or tray
5. Device record opened
6. Device plugged in for data capture

The barcode ties the device to its system record.

---

# 7. USB Device Data Capture

When a device is connected, the system should capture available data including:

**Identifiers**

- IMEI
- Serial number

**Device info**

- Model
- Model identifier
- Storage
- Colour

**Battery**

- Battery health
- Cycle count

**Software**

- OS version
- Lock/passcode state

**Security**

- Activation lock status
- Jailbreak status

Any returned USB data should be stored even if partial.

---

# 8. Diagnostics

Devices undergo diagnostics using:

- Blackbelt360
- Phonecheck

Diagnostic reports must be stored against the device.

Diagnostics reports are **mandatory before listing devices for sale**.

---

# 9. Device Lifecycle

Example lifecycle flow:


Expected
↓
Arrived
↓
USB Data Captured
↓
Diagnostics Complete
↓
Decision Stage


Decision outcomes:


Repair Queue
Third-party Repair
Inventory Ready
Trade-in Channel
Donor Device
Return to Customer


Later stages:


Listed
Sold
Warranty Return
Closed


Lifecycle transitions must be controlled by the system.

---

# 10. Device Status Tracking

Devices have a visible lifecycle status.

Statuses are used for:

- UI display
- filtering queues
- workflow management

Example statuses:


Arrived
Awaiting Diagnostics
Awaiting Parts
Repair Queue
Awaiting Third-party Return
Ready for Sale
Listed
Sold
Donor Device
Returned


---

# 11. Workflow Alerts and Queues

The system must provide operational queues.

Example technician queues:


Devices awaiting diagnostics
Devices awaiting repair
Devices awaiting parts
Devices awaiting third-party return
Donor devices awaiting harvesting


Example admin queues:


Devices awaiting counter-offer response
Devices ready to list
Devices stuck in workflow


Devices stuck in a stage should trigger alerts.

---

# 12. Counter-Offer Policy

Counter-offers should be used sparingly to avoid negative marketplace KPIs.

Do not counter-offer for:

- minor cosmetic scratches
- cheap repairs (speakers, taptic engine, microphone)

Counter-offers should be used when:

- screen cracked
- severe cosmetic damage
- expensive repairs required

---

# 13. Repairs

Repairs may occur:

- internally
- via third-party repair providers

Repair records must include:

- repair type
- parts used
- labour
- repair outcome

---

# 14. Third-Party Repairs

Devices may be sent to external repair providers.

Recorded data includes:

- provider
- repair type
- sent date
- expected return
- actual return
- repair cost

Optional shipping data:

- carrier
- tracking number

---

# 15. Parts Ordering

All repair parts must be recorded against the device.

Required fields:

- part name
- supplier
- cost
- order status
- expected arrival
- actual arrival

This allows full cost tracking.

---

# 16. Donor Device System

Devices that cannot be economically repaired become **donor devices**.

Example:


Device DEV-000123
Status: Donor Device


Parts available and removed must be tracked.

When a part is harvested:

- donor device recorded
- receiving device recorded
- internal part value assigned

---

# 17. Inventory Model

Inventory tracks **individual devices**, not SKU quantities.

Each device is unique and must store:

- IMEI
- grade
- repair history
- cost basis
- sale price

---

# 18. Device Grading

Inventory devices are graded as:


Excellent
Good
Fair


Customer declared condition is stored separately.

---

# 19. Sales Channels

The system must support multiple channels including:

- BackMarket
- eBay
- Amazon
- Shopify
- Wholesale
- POS

Inventory items remain channel-agnostic.

Listings are attached per channel.

---

# 20. Pricing

The platform will support a pricing module.

Pricing flow:


Pricer suggested price
↓
Marketplace listing price
↓
Final sale price


Marketplace constraints (BackMarket backbox etc.) must be supported.

---

# 21. Profitability

The system must calculate:

**Predicted profit**


Sale estimate

buy price

estimated repair

marketplace fees


**Actual profit**


Sale price

buy price

parts

shipping

marketplace fees


---

# 22. Accounting

The platform must support accounting outputs including:

- VAT Margin Book
- purchase records
- sales records
- quarterly VAT summaries

Businesses may have different VAT periods.

---

# 23. Warranty Returns

If a sold device returns:

The same device record is **reopened**.

Return records include:

- return reason
- return type (warranty/out-of-warranty)
- diagnostic findings
- repair performed
- resolution

---

# 24. Attachments

Device records must support:

Mandatory files:

- diagnostics reports
- CheckMEND reports

Optional files:

- photos
- repair images
- customer images

---

# 25. Internal Notes

Devices must support structured notes including:

- author
- timestamp
- note category
- note content

Categories may include diagnostics, repair, customer, warranty, etc.

---

# 26. Manual Device Creation

Devices must be creatable manually for:

- walk-in purchases
- supplier purchases
- donor phones
- dead devices

Minimum required data:

- make
- model
- condition
- source
- buy price