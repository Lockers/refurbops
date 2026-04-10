from fastapi import APIRouter, Depends

from app.api.deps import AuthenticatedRequestContext, require_permission, require_platform_owner_context
from app.db.mongo import get_database
from app.foundation.businesses.schemas import (
    BusinessMembershipCreateRequest,
    BusinessMembershipArchiveResponse,
    BusinessMembershipCreateResponse,
    BusinessMembershipsReadResponse,
    BusinessReadResponse,
    BusinessUpdateRequest,
    BusinessUpdateResponse,
    BusinessSiteCreateRequest,
    BusinessSiteCreateResponse,
    BusinessSiteCapacityUpdateRequest,
    BusinessSiteCapacityUpdateResponse,
    BusinessSitesReadResponse,
    BusinessActivateResponse,
    BusinessUserSuspendResponse,
    BusinessUserReactivateResponse,
    ProvisionInitialBusinessRequest,
    ProvisionInitialBusinessResponse,
)
from app.foundation.businesses.service import business_provisioning_service


businesses_router = APIRouter(prefix="/foundation/businesses", tags=["foundation:businesses"])


@businesses_router.post("/provision-initial", response_model=ProvisionInitialBusinessResponse)
async def provision_initial_business(
    payload: ProvisionInitialBusinessRequest,
    context: AuthenticatedRequestContext = Depends(require_platform_owner_context),
) -> ProvisionInitialBusinessResponse:
    database = await get_database()
    return await business_provisioning_service.provision_initial_business(
        database=database,
        context=context,
        payload=payload,
    )


@businesses_router.get("/{business_public_id}", response_model=BusinessReadResponse)
async def get_business(
    business_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("business.read")),
) -> BusinessReadResponse:
    database = await get_database()
    return await business_provisioning_service.get_business(
        database=database,
        context=context,
        business_public_id=business_public_id,
    )


@businesses_router.patch("/{business_public_id}", response_model=BusinessUpdateResponse)
async def update_business(
    business_public_id: str,
    payload: BusinessUpdateRequest,
    context: AuthenticatedRequestContext = Depends(require_permission("business.manage")),
) -> BusinessUpdateResponse:
    database = await get_database()
    return await business_provisioning_service.update_business(
        database=database,
        context=context,
        business_public_id=business_public_id,
        payload=payload,
    )


@businesses_router.get("/{business_public_id}/sites", response_model=BusinessSitesReadResponse)
async def list_business_sites(
    business_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("site.read")),
) -> BusinessSitesReadResponse:
    database = await get_database()
    return await business_provisioning_service.list_business_sites(
        database=database,
        context=context,
        business_public_id=business_public_id,
    )


@businesses_router.post("/{business_public_id}/sites", response_model=BusinessSiteCreateResponse)
async def create_business_site(
    business_public_id: str,
    payload: BusinessSiteCreateRequest,
    context: AuthenticatedRequestContext = Depends(require_permission("site.manage")),
) -> BusinessSiteCreateResponse:
    database = await get_database()
    return await business_provisioning_service.create_business_site(
        database=database,
        context=context,
        business_public_id=business_public_id,
        payload=payload,
    )


@businesses_router.get("/{business_public_id}/memberships", response_model=BusinessMembershipsReadResponse)
async def list_business_memberships(
    business_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("membership.read")),
) -> BusinessMembershipsReadResponse:
    database = await get_database()
    return await business_provisioning_service.list_business_memberships(
        database=database,
        context=context,
        business_public_id=business_public_id,
    )


@businesses_router.post("/{business_public_id}/memberships", response_model=BusinessMembershipCreateResponse)
async def add_business_membership(
    business_public_id: str,
    payload: BusinessMembershipCreateRequest,
    context: AuthenticatedRequestContext = Depends(require_permission("membership.manage")),
) -> BusinessMembershipCreateResponse:
    database = await get_database()
    return await business_provisioning_service.add_business_membership(
        database=database,
        context=context,
        business_public_id=business_public_id,
        payload=payload,
    )


@businesses_router.delete("/{business_public_id}/memberships/{membership_public_id}", response_model=BusinessMembershipArchiveResponse)
async def archive_business_membership(
    business_public_id: str,
    membership_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("membership.manage")),
) -> BusinessMembershipArchiveResponse:
    database = await get_database()
    return await business_provisioning_service.archive_business_membership(
        database=database,
        context=context,
        business_public_id=business_public_id,
        membership_public_id=membership_public_id,
    )


@businesses_router.patch("/{business_public_id}/site-capacity", response_model=BusinessSiteCapacityUpdateResponse)
async def update_business_site_capacity(
    business_public_id: str,
    payload: BusinessSiteCapacityUpdateRequest,
    context: AuthenticatedRequestContext = Depends(require_platform_owner_context),
) -> BusinessSiteCapacityUpdateResponse:
    database = await get_database()
    return await business_provisioning_service.update_business_site_capacity(
        database=database,
        context=context,
        business_public_id=business_public_id,
        payload=payload,
    )


@businesses_router.post("/{business_public_id}/activate", response_model=BusinessActivateResponse)
async def activate_business(
    business_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("business.manage")),
) -> BusinessActivateResponse:
    database = await get_database()
    return await business_provisioning_service.activate_business(
        database=database,
        context=context,
        business_public_id=business_public_id,
    )


@businesses_router.post("/{business_public_id}/users/{user_public_id}/suspend", response_model=BusinessUserSuspendResponse)
async def suspend_business_user(
    business_public_id: str,
    user_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("membership.manage")),
) -> BusinessUserSuspendResponse:
    database = await get_database()
    return await business_provisioning_service.suspend_business_user(
        database=database,
        context=context,
        business_public_id=business_public_id,
        user_public_id=user_public_id,
    )


@businesses_router.post("/{business_public_id}/users/{user_public_id}/reactivate", response_model=BusinessUserReactivateResponse)
async def reactivate_business_user(
    business_public_id: str,
    user_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("membership.manage")),
) -> BusinessUserReactivateResponse:
    database = await get_database()
    return await business_provisioning_service.reactivate_business_user(
        database=database,
        context=context,
        business_public_id=business_public_id,
        user_public_id=user_public_id,
    )
