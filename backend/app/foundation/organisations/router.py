from fastapi import APIRouter, Depends

from app.api.deps import AuthenticatedRequestContext, require_permission
from app.db.mongo import get_database
from app.foundation.organisations.schemas import (
    OrganisationReadResponse,
    OrganisationUpdateRequest,
    OrganisationUpdateResponse,
)
from app.foundation.organisations.service import organisation_service


organisations_router = APIRouter(prefix="/foundation/organisations", tags=["foundation:organisations"])


@organisations_router.get("/{organisation_public_id}", response_model=OrganisationReadResponse)
async def get_organisation(
    organisation_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("organisation.read")),
) -> OrganisationReadResponse:
    database = await get_database()
    return await organisation_service.get_organisation(
        database=database,
        context=context,
        organisation_public_id=organisation_public_id,
    )


@organisations_router.patch("/{organisation_public_id}", response_model=OrganisationUpdateResponse)
async def update_organisation(
    organisation_public_id: str,
    payload: OrganisationUpdateRequest,
    context: AuthenticatedRequestContext = Depends(require_permission("organisation.manage")),
) -> OrganisationUpdateResponse:
    database = await get_database()
    return await organisation_service.update_organisation(
        database=database,
        context=context,
        organisation_public_id=organisation_public_id,
        payload=payload,
    )
