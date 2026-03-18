# RefurbOps Frontend Phase 1 Integration Plan

This document turns the current repo review into a concrete implementation plan for the first integrated frontend slice.

## Objectives

Phase 1 should deliver a usable operator-facing frontend for the backend that already exists.

Primary outcomes:

1. add application routing
2. add business context instead of hardcoded tenant usage
3. centralise API communication through one client
4. complete the setup -> inbound queue path
5. expose inbound queue filters, pagination, sync feedback, and inbound detail
6. add a lightweight application shell with API health visibility

## Scope included in this phase

### Frontend

- Setup route
- Inbound queue route
- Inbound order detail route
- Shared business context
- Shared app shell
- Shared loading, error, and empty states
- Unified HTTP client
- Typed inbound list/detail/sync contracts aligned to backend responses

### Backend usage

The frontend consumes the existing endpoints only:

- `GET /health`
- `GET /api/setup/status`
- `POST /api/setup/bootstrap`
- `POST /api/inbound/backmarket/sync`
- `GET /api/inbound`
- `GET /api/inbound/{inbound_id}`

## Proposed frontend structure

```text
frontend/src/
  app/
    layout/
      AppShell.tsx
    providers/
      BusinessProvider.tsx
    App.tsx
  components/
    layout/
      PageShell.tsx
    ui/
      EmptyState.tsx
      ErrorState.tsx
      LoadingState.tsx
  pages/
    SetupPage.tsx
    InboundPage.tsx
    InboundDetailPage.tsx
  services/
    api/
      client.ts
    inboundApi.ts
    setupApi.ts
  types/
    inbound.ts
    setup.ts
```

## Implementation order

### Step 1

Replace the current single-screen app entry with a small route-aware application controller.

### Step 2

Introduce `BusinessProvider` backed by local storage so all business-scoped requests use the same tenant source.

### Step 3

Refactor HTTP calls behind a single Axios client with consistent base URL defaults and error shaping.

### Step 4

Upgrade the inbound queue page to support:

- sync action
- backend-supported filters
- pagination
- row click navigation
- success and error feedback

### Step 5

Add an inbound detail page that displays the full backend DTO in operational cards.

### Step 6

Wrap business routes in an app shell that shows:

- current business
- API health
- primary navigation

## Next phase after this one

The next backend/frontend vertical slice should implement the documented Module 1 workflow:

1. Arrived action
2. device creation
3. generated `device_id`
4. status initialisation
5. route to device detail

That will turn the inbound page from a queue viewer into the true workflow entry point.
