# Codex Agent Rules

This repository follows a strict architecture and workflow.

Codex must respect the rules below when generating code or patches.

---

# Architecture Rules

The platform uses a layered backend architecture.

Structure:

backend/app/
- api/routers
- schemas
- services
- repositories
- integrations
- core
- models
- utils

Rules:

- routers must not contain business logic
- services contain workflow logic
- repositories handle database access
- integrations handle external APIs

---

# Development Principles

1. Do not rewrite existing modules unless necessary.
2. Prefer minimal patches where possible.
3. When changes affect multiple areas, provide full file updates.
4. Always include comments and docstrings in code.
5. Follow existing naming conventions.

---

# Workflow Model

Devices move through a lifecycle.

Status transitions must follow the defined status model in:


docs/status_model_v1.md


Do not introduce new statuses without updating the status model.

---

# Database Rules

MongoDB is used.

All business data must include:


business_id


Queries must always filter by business_id unless the operation is platform-level.

---

# External Integrations

Integrations should live in:


backend/app/integrations/


Examples:

- BackMarket API
- CheckMEND
- carrier tracking
- diagnostics imports

Do not mix integration logic into service or router layers.

---

# Code Quality

Code must be:

- production quality
- readable
- well documented

Avoid simplified demo implementations.

---

# Documentation

Major architecture decisions must be reflected in the documentation inside:


docs/


before large code changes are made.

---

# First Module Focus

Current development focus:


BackMarket inbound sync


See:


docs/backmarket_inbound_sync_spec_v2.md


for implementation requirements.

---
Your repo should now look like this
refurbops/
  backend/
  frontend/
  docs/
    ai_working_rules.md
    system_blueprint.md
    technical_architecture.md
    data_model_v1.md
    status_model_v1.md
    module_plan_v1.md
    backmarket_inbound_sync_spec_v2.md
    project_structure.md

  scripts/

  README.md
  AGENTS.md
  .gitignore
