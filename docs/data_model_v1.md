# RefurbOps Platform — Data Model v1

This document defines the initial MongoDB data model for the RefurbOps platform.

The goal is to provide a clean, scalable foundation for:

- intake workflows
- device lifecycle tracking
- repairs
- donor devices
- parts ordering
- inventory
- marketplace sales
- VAT accounting
- warranty returns

The system follows a **lean core device document pattern**, with lifecycle events stored in separate collections.

---

# 1. Multi-Tenant Model

All business-owned records must include:


business_id


This ensures tenant isolation.

Example:


{
"business_id": "biz_001"
}


All queries must filter by `business_id`.

---

# 2. Core Collections

Initial collections for v1:


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


---

# 3. Businesses

Collection:


businesses


Example document:

```json
{
  "_id": "biz_001",
  "name": "RepairedTech Ltd",
  "vat_registered": true,
  "vat_scheme": "margin",
  "vat_period": "quarterly",
  "vat_period_start": "2026-01-01",
  "created_at": "2026-03-01"
}
4. Users

Collection:

users

Example document:

{
  "_id": "usr_001",
  "business_id": "biz_001",
  "name": "Tom",
  "email": "tom@company.com",
  "role": "technician",
  "active": true,
  "created_at": "2026-03-01"
}

Roles:

platform_owner
business_admin
technician
viewer
5. Inbound Orders

Collection:

inbound_orders

Purpose:

Stores inbound context (BackMarket trade-in, supplier purchase etc).

Example:

{
  "_id": "inb_001",
  "business_id": "biz_001",
  "source": "backmarket_tradein",
  "source_reference": "BM-12345",
  "customer": {
    "name": "John Smith",
    "address": "10 High Street"
  },
  "expected_device": {
    "make": "Apple",
    "model": "iPhone 14",
    "condition": "Good",
    "buy_price": 210
  },
  "created_at": "2026-03-10"
}

Relationship:

Inbound Order
   ↓
Device
6. Devices (Core Lifecycle Record)

Collection:

devices

This is the primary workflow object.

Example document:

{
  "_id": "DEV-00001234",
  "business_id": "biz_001",
  "inbound_order_id": "inb_001",

  "status": "arrived",
  "status_updated_at": "2026-03-10T10:15:00Z",

  "route": "sale",

  "location": "Testing Bench",

  "assigned_user_id": null,

  "flags": ["repair_required"],

  "customer_snapshot": {
    "name": "John Smith",
    "address": "10 High Street"
  },

  "device_expected": {
    "make": "Apple",
    "model": "iPhone 14",
    "condition": "Good",
    "buy_price": 210
  },

  "usb_data": {
    "imei": "356789012345678",
    "serial": "C02XYZ1234",
    "model_identifier": "iPhone15,2",
    "storage": "256GB",
    "colour": "Purple",
    "battery_health": 88,
    "cycle_count": 510
  },

  "usb_raw_payload": {},

  "diagnostics_summary": {
    "provider": "Blackbelt",
    "result": "pass",
    "tested_at": "2026-03-10"
  },

  "checkmend_summary": {
    "status": "clear",
    "checked_at": "2026-03-10",
    "report_reference": "CM123456",
    "blacklisted": false,
    "finance_issue": false
  },

  "financial_snapshot": {
    "buy_price": 210,
    "estimated_repair_cost": 25,
    "actual_repair_cost": 0,
    "predicted_profit": 120,
    "actual_profit": null
  },

  "sale_readiness": {
    "diagnostics_report_attached": true,
    "checkmend_complete": true,
    "final_grade_set": false,
    "ready_for_sale": false
  },

  "notes_count": 3,
  "attachments_count": 2,

  "created_at": "2026-03-10",
  "updated_at": "2026-03-10"
}
7. Device Notes

Collection:

device_notes

Example:

{
  "_id": "note_001",
  "business_id": "biz_001",
  "device_id": "DEV-00001234",
  "note_type": "diagnostics",
  "content": "Screen scratched heavily",
  "author_user_id": "usr_001",
  "created_at": "2026-03-10"
}
8. Device Attachments

Collection:

device_attachments

Example:

{
  "_id": "att_001",
  "business_id": "biz_001",
  "device_id": "DEV-00001234",
  "attachment_type": "diagnostics_report",
  "file_path": "/files/reports/diag_001.pdf",
  "uploaded_by": "usr_001",
  "uploaded_at": "2026-03-10"
}

Types:

diagnostics_report
checkmend_report
customer_photo
repair_photo
sale_photo
9. Repair Jobs

Collection:

repair_jobs

Example:

{
  "_id": "rep_001",
  "business_id": "biz_001",
  "device_id": "DEV-00001234",
  "repair_type": "screen_replacement",
  "status": "awaiting_parts",
  "internal": true,
  "created_at": "2026-03-10"
}
10. Parts Orders

Collection:

parts_orders

Example:

{
  "_id": "prt_001",
  "business_id": "biz_001",
  "device_id": "DEV-00001234",
  "repair_job_id": "rep_001",
  "part_name": "iPhone 14 OLED Screen",
  "supplier": "ReplaceBase",
  "cost": 32,
  "status": "ordered",
  "expected_arrival": "2026-03-12"
}
11. Donor Parts

Collection:

donor_parts

Example:

{
  "_id": "don_001",
  "business_id": "biz_001",
  "donor_device_id": "DEV-00001111",
  "part_type": "taptic_engine",
  "status": "available",
  "internal_value": 6
}
12. Inventory Items

Collection:

inventory_items

Example:

{
  "_id": "inv_001",
  "business_id": "biz_001",
  "device_id": "DEV-00001234",
  "grade": "Good",
  "battery_health": 88,
  "ready_for_sale": true
}
13. Sales

Collection:

sales

Example:

{
  "_id": "sale_001",
  "business_id": "biz_001",
  "device_id": "DEV-00001234",
  "channel": "backmarket",
  "order_reference": "BM-56789",
  "customer": {
    "name": "Jane Doe",
    "address": "22 King Street"
  },
  "sale_price": 489,
  "sold_at": "2026-03-15"
}
14. Returns

Collection:

returns

Example:

{
  "_id": "ret_001",
  "business_id": "biz_001",
  "device_id": "DEV-00001234",
  "return_type": "warranty",
  "reason": "Camera fault",
  "returned_at": "2026-04-02"
}
15. VAT Margin Entries

Collection:

vat_margin_entries

Example:

{
  "_id": "vat_001",
  "business_id": "biz_001",
  "device_id": "DEV-00001234",
  "purchase_price": 210,
  "sale_price": 489,
  "margin": 279,
  "vat_due": 46.50,
  "sale_date": "2026-03-15"
}
16. System Counters

Collection:

system_counters

Used for generating sequential IDs.

Example:

{
  "_id": "device_id",
  "next_value": 1235
}

Device ID format:

DEV-00001235
17. Index Strategy

Important indexes:

Devices:

device_id
business_id
imei
status
route
location

Repairs:

device_id
status

Sales:

device_id
channel

Notes:

device_id