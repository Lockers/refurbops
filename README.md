# RefurbOps Platform

RefurbOps is a multi-business refurb and repair operations platform designed for mobile refurb businesses.

The system manages the full lifecycle of devices including:

- inbound trade-ins (BackMarket integration)
- barcode-based device tracking
- diagnostics and testing
- repair workflows
- donor device / parts harvesting
- inventory management
- multi-channel sales
- VAT margin accounting
- warranty returns
- profitability tracking

The platform is designed to be used daily by refurb technicians while also being suitable as a SaaS platform for multiple refurb businesses.

---

# Architecture

Tech stack:

Backend:
- Python
- FastAPI
- MongoDB

Frontend:
- React
- TypeScript
- Vite

The platform uses a **multi-tenant architecture** where each business operates independently using a shared platform.

---

# Repository Structure


refurbops/
backend/
frontend/
docs/
scripts/


### backend
Python API, services, and integrations.

### frontend
React application for the operational interface.

### docs
Architecture and design documentation.

### scripts
Utility scripts and developer tools.

---

# Development Approach

The platform is built using **vertical modules** rather than isolated backend/frontend work.

Development order follows:

1. BackMarket inbound sync
2. Device intake and barcode workflow
3. Device lifecycle management
4. Repairs and parts
5. Inventory
6. Sales and accounting

---

# Documentation

All architecture and planning documents are stored in:


docs/


These include:

- system blueprint
- data model
- workflow status model
- inbound sync design
- module implementation plan

---

# Development Environment

Local development:

- backend runs locally
- frontend runs locally
- MongoDB runs locally

Future production target:

- cloud backend
- cloud frontend
- MongoDB Atlas
- object storage for files

---

# Current Build Focus

The first implementation module is:


BackMarket inbound sync
→ inbound queue
→ arrived action
→ device creation
→ barcode label

---

# Repository Structure
