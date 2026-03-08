from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas.inbound import InboundQueueRow

from app.core.database import get_database
from app.integrations.backmarket.client import (
    BackMarketAuthenticationError,
    BackMarketClient,
    BackMarketClientError,
    BackMarketConfigurationError,
    BackMarketRateLimitError,
    BackMarketResponseError,
    BackMarketTransientError,
)
from app.repositories.business_repository import BusinessRepository
from app.repositories.inbound_order_repository import InboundOrderRepository
from app.repositories.sync_state_repository import SyncStateRepository
from app.schemas.inbound import (
    InboundListResponse,
    InboundOrderDocument,
    InboundSyncRequest,
    InboundSyncResult,
)
from app.services.inbound_sync_service import InboundSyncService

router = APIRouter()


def get_inbound_sync_service(
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> InboundSyncService:
    """
    Build the Module 01 inbound sync service and its dependencies.

    Keeping this wiring local to the router is fine for the current scaffold.
    If dependency setup grows later, it can be moved into a dedicated provider
    module without changing route behavior.
    """
    business_repo = BusinessRepository(database)
    inbound_repo = InboundOrderRepository(database)
    sync_state_repo = SyncStateRepository(database)
    backmarket_client = BackMarketClient()

    return InboundSyncService(
        business_repo=business_repo,
        inbound_repo=inbound_repo,
        sync_state_repo=sync_state_repo,
        backmarket_client=backmarket_client,
    )


@router.post(
    "/backmarket/sync",
    response_model=InboundSyncResult,
    status_code=status.HTTP_200_OK,
)
async def sync_backmarket_inbound_orders(
    payload: InboundSyncRequest,
    service: InboundSyncService = Depends(get_inbound_sync_service),
) -> InboundSyncResult:
    """
    Trigger a manual incremental sync of Back Market buyback orders.

    Business scoping is explicit for now via the request body. Later this should
    come from auth and tenant context.
    """
    try:
        result = await service.sync_backmarket_buyback(payload.business_id)
        return InboundSyncResult.model_validate(result)

    except BackMarketConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except BackMarketAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    except BackMarketRateLimitError as exc:
        detail: dict[str, Any] = {"message": str(exc)}
        if exc.retry_after_seconds is not None:
            detail["retry_after_seconds"] = exc.retry_after_seconds

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        ) from exc

    except BackMarketTransientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except BackMarketResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except BackMarketClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=InboundListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_inbound_orders(
    business_id: str = Query(..., description="Business identifier."),
    external_status: str | None = Query(None),
    market: str | None = Query(None),
    has_tracking: bool | None = Query(None),
    tracking_status_group: str | None = Query(None),
    likely_arrival_bucket: str | None = Query(None),
    arrived_clicked: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    service: InboundSyncService = Depends(get_inbound_sync_service),
) -> InboundListResponse:
    """
    Return the active inbound queue for a business.

    Default queue behavior is handled in the repository:
    - device_created = false
    - hidden_from_inbound = false
    """
    filters: dict[str, Any] = {
        "external_status": external_status,
        "market": market,
        "has_tracking": has_tracking,
        "tracking_status_group": tracking_status_group,
        "likely_arrival_bucket": likely_arrival_bucket,
        "arrived_clicked": arrived_clicked,
    }

    items, total = await service.get_inbound_queue(
        business_id=business_id,
        filters=filters,
        page=page,
        page_size=page_size,
    )

    return InboundListResponse(
        items=[InboundQueueRow.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{inbound_id}",
    response_model=InboundOrderDocument,
    status_code=status.HTTP_200_OK,
)
async def get_inbound_order(
    inbound_id: str,
    business_id: str = Query(..., description="Business identifier."),
    service: InboundSyncService = Depends(get_inbound_sync_service),
) -> InboundOrderDocument:
    """
    Return a single inbound order by Mongo `_id`, scoped to the business.
    """
    order = await service.get_inbound_order(
        business_id=business_id,
        inbound_id=inbound_id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inbound order not found.",
        )

    return InboundOrderDocument.model_validate(
        {
            **order,
            "_id": str(order["_id"]),
        }
    )
