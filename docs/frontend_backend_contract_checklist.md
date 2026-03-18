# Frontend and Backend Contract Checklist

This document records the current backend endpoint surface and the frontend work required to keep the UI aligned exactly to those live contracts.

## Current backend routes

- `GET /`
- `GET /health`
- `GET /api/setup/status`
- `POST /api/setup/bootstrap`
- `POST /api/inbound/backmarket/sync`
- `GET /api/inbound`
- `GET /api/inbound/{inbound_id}`

## Endpoint coverage checklist

### Implemented

- [x] health endpoint consumed by frontend shell
- [x] setup status consumed on app load
- [x] setup bootstrap submitted from setup page
- [x] inbound sync triggered from queue page
- [x] inbound list consumed with all backend-supported filters
- [x] inbound detail consumed from queue row navigation

### Tightening required for exact contract alignment

- [x] consume backend root metadata endpoint in the frontend shell
- [x] align inbound and setup TypeScript types with backend nullable/required fields
- [x] surface richer backend error metadata for sync failures, including retry timing when present
- [x] render the remaining inbound detail payload blocks that already exist in the backend DTO

## Files touched for contract alignment

- `frontend/src/services/api/client.ts`
- `frontend/src/types/inbound.ts`
- `frontend/src/types/setup.ts`
- `frontend/src/app/layout/AppShell.tsx`
- `frontend/src/pages/InboundPage.tsx`
- `frontend/src/pages/InboundDetailPage.tsx`

## Future recommendation

The next step after this manual alignment pass should be generating frontend API contracts from the FastAPI OpenAPI schema so future backend changes cannot silently drift away from the frontend.
