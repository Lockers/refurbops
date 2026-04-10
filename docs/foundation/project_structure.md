# RefurbOps Platform — Project Structure

This document defines the base repository and environment structure for the RefurbOps platform.

The goal is to keep the system organised from day one and avoid structural churn later.

---

# 1. Project Approach

The platform will be built as a **single repository** with clearly separated backend, frontend, documentation, and scripts.

Development will run **locally first**, but the project must always be structured with **future cloud deployment in mind**.

---

# 2. Repository Structure

Recommended root structure:

```text
refurbops/
  backend/
  frontend/
  docs/
  scripts/
3. Backend Structure

Recommended backend structure:

backend/
  app/
    api/
      routers/
    core/
    schemas/
    services/
    repositories/
    integrations/
    models/
    utils/
    main.py

  tests/
  requirements.txt
  .env
  .env.example
Responsibilities
api/routers/

HTTP endpoints only.

core/

Application configuration, database connection, auth helpers, shared settings.

schemas/

Pydantic request/response models and validation schemas.

services/

Business logic and workflow orchestration.

repositories/

MongoDB access layer.

integrations/

External systems:

BackMarket API

barcode label generation

printer integration

carrier tracking

diagnostics imports

CheckMEND

models/

Shared enums, constants, internal typed models where useful.

utils/

Small reusable helper functions only.

tests/

Later automated tests for stable business logic.

4. Frontend Structure

Recommended frontend structure:

frontend/
  src/
    app/
    routes/
    pages/
    components/
    features/
    services/
    hooks/
    types/
    utils/
    main.tsx

  package.json
  .env
  .env.example
Responsibilities
pages/

Top-level screens such as:

inbound queue

device detail

repair queue

inventory

donor devices

sales

returns

VAT/accounting

components/

Reusable UI components.

features/

Feature-grouped UI logic.

services/

API client layer.

hooks/

Reusable React hooks.

types/

Shared frontend TypeScript types.

routes/

Routing configuration and route guards.

5. Docs Structure

All planning and architecture documents should live in:

docs/

Recommended contents:

docs/
  ai_working_rules.md
  system_blueprint.md
  technical_architecture.md
  data_model_v1.md
  status_model_v1.md
  module_plan_v1.md
  backmarket_inbound_sync_spec_v2.md
  project_structure.md

This folder becomes the long-term reference point for the project.

6. Scripts Structure

Utility scripts should live in:

scripts/

Examples:

local setup helpers

DB seed helpers

migration/export tools

one-off data repair scripts

Do not scatter standalone scripts randomly across backend/frontend.

7. Environment Strategy

The project will support local development now and cloud deployment later.

Local development

backend runs locally

frontend runs locally

MongoDB runs locally

Future production

backend deployed in cloud

frontend deployed in cloud

database hosted in managed cloud environment

object/file storage hosted in cloud

8. Environment Files

Both backend and frontend should use environment files.

Backend

Files:

backend/.env
backend/.env.example
Frontend

Files:

frontend/.env
frontend/.env.example
Rule

real secrets go in .env

safe placeholders go in .env.example

.env files must not be committed

9. Backend Environment Variables

Expected backend variables later may include:

APP_ENV
APP_HOST
APP_PORT

MONGO_URI
MONGO_DB_NAME

JWT_SECRET_KEY

BACKMARKET_BASE_URL
BACKMARKET_API_KEY

FILE_STORAGE_MODE
FILE_STORAGE_PATH

CHECKMEND_API_KEY
CHECKMEND_BASE_URL

Not all of these need to exist immediately, but structure should allow them.

10. Frontend Environment Variables

Expected frontend variables may include:

VITE_API_BASE_URL
VITE_APP_ENV

Keep frontend config minimal.

11. Local vs Cloud Design Rule

Even though development starts locally, all major architectural decisions must assume the final destination is:

cloud frontend
cloud backend
cloud database
optional local hardware integrations

This is especially important for:

barcode printing

scanner handling

USB phone reading

carrier tracking

diagnostics imports

The main web application should remain cloud-ready, while optional local hardware bridges can be added later.

12. IDE Usage

Planned development workflow:

PyCharm for backend

VS Code for frontend

This is fully compatible with a single-repo structure.

Recommended usage:

open backend/ in PyCharm

open frontend/ in VS Code

keep both under the same Git repository

13. Initial Build Focus

The first implementation work should happen in this order:

1. backend project skeleton
2. frontend project skeleton
3. Mongo connection + config
4. BackMarket inbound sync module
5. Arrived → device creation flow
6. barcode label generation
7. device detail page
14. Structural Rules

To keep the project maintainable:

keep business logic out of routers

keep DB access inside repositories

keep external integrations isolated

keep docs updated when major architecture decisions are made

do not create random top-level folders without agreement

15. Final Principle

The project structure must support:

local development now

cloud deployment later

multi-business tenancy

clean module growth over time

The structure should stay stable even as modules are added.