from fastapi import APIRouter, Depends

from app.api.deps import AuthenticatedRequestContext, require_permission
from app.db.mongo import get_database
from app.foundation.sites.schemas import SiteReadResponse, SiteUpdateRequest, SiteUpdateResponse
from app.foundation.sites.service import site_service


sites_router = APIRouter(prefix="/foundation/sites", tags=["foundation:sites"])


@sites_router.get("/{site_public_id}", response_model=SiteReadResponse)
async def get_site(
    site_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("site.read")),
) -> SiteReadResponse:
    database = await get_database()
    return await site_service.get_site(
        database=database,
        context=context,
        site_public_id=site_public_id,
    )


@sites_router.patch("/{site_public_id}", response_model=SiteUpdateResponse)
async def update_site(
    site_public_id: str,
    payload: SiteUpdateRequest,
    context: AuthenticatedRequestContext = Depends(require_permission("site.manage")),
) -> SiteUpdateResponse:
    database = await get_database()
    return await site_service.update_site(
        database=database,
        context=context,
        site_public_id=site_public_id,
        payload=payload,
    )
