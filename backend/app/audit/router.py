from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import AuthenticatedRequestContext, require_permission
from app.audit.schemas import BusinessAuditEventsReadResponse
from app.audit.service import audit_service
from app.db.mongo import get_database


audit_router = APIRouter(prefix="/audit", tags=["audit"])


@audit_router.get("/businesses/{business_public_id}/events", response_model=BusinessAuditEventsReadResponse)
async def list_business_audit_events(
    business_public_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    event_types: Annotated[list[str] | None, Query()] = None,
    before: str | None = Query(default=None),
    context: AuthenticatedRequestContext = Depends(require_permission("business.read")),
) -> BusinessAuditEventsReadResponse:
    database = await get_database()
    return await audit_service.list_business_events(
        database=database,
        context=context,
        business_public_id=business_public_id,
        limit=limit,
        event_types=event_types,
        before=before,
    )
