from fastapi import APIRouter, Depends

from app.api.deps import AuthenticatedRequestContext, require_permission, require_platform_owner_context
from app.db.mongo import get_database
from app.foundation.subscriptions.schemas import (
    BusinessSubscriptionHistoryResponse,
    BusinessSubscriptionReadResponse,
    BusinessSubscriptionUpsertRequest,
    BusinessSubscriptionUpsertResponse,
)
from app.foundation.subscriptions.service import subscription_service


subscriptions_router = APIRouter(prefix="/foundation/businesses", tags=["foundation:subscriptions"])


@subscriptions_router.get("/{business_public_id}/subscription", response_model=BusinessSubscriptionReadResponse)
async def get_business_subscription(
    business_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("subscription.read")),
) -> BusinessSubscriptionReadResponse:
    database = await get_database()
    return await subscription_service.get_business_subscription(
        database=database,
        context=context,
        business_public_id=business_public_id,
    )


@subscriptions_router.patch("/{business_public_id}/subscription", response_model=BusinessSubscriptionUpsertResponse)
async def upsert_business_subscription(
    business_public_id: str,
    payload: BusinessSubscriptionUpsertRequest,
    context: AuthenticatedRequestContext = Depends(require_platform_owner_context),
) -> BusinessSubscriptionUpsertResponse:
    database = await get_database()
    return await subscription_service.upsert_business_subscription(
        database=database,
        context=context,
        business_public_id=business_public_id,
        payload=payload,
    )


@subscriptions_router.get("/{business_public_id}/subscription/history", response_model=BusinessSubscriptionHistoryResponse)
async def get_business_subscription_history(
    business_public_id: str,
    context: AuthenticatedRequestContext = Depends(require_permission("subscription.read")),
) -> BusinessSubscriptionHistoryResponse:
    database = await get_database()
    return await subscription_service.get_business_subscription_history(
        database=database,
        context=context,
        business_public_id=business_public_id,
    )
