from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.repositories.business_repository import BusinessRepository
from app.repositories.user_repository import UserRepository
from app.schemas.setup import (
    SetupBootstrapRequest,
    SetupBootstrapResponse,
    SetupStatusResponse,
)
from app.services.setup_service import SetupService

router = APIRouter()


def get_setup_service(
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> SetupService:
    """
    Build setup service and repository dependencies for the setup routes.
    """
    business_repo = BusinessRepository(database)
    user_repo = UserRepository(database)

    return SetupService(
        business_repo=business_repo,
        user_repo=user_repo,
    )


@router.get(
    "/status",
    response_model=SetupStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_setup_status(
    service: SetupService = Depends(get_setup_service),
) -> SetupStatusResponse:
    """
    Return whether the platform has already been bootstrapped.
    """
    return await service.get_setup_status()


@router.post(
    "/bootstrap",
    response_model=SetupBootstrapResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bootstrap_system(
    payload: SetupBootstrapRequest,
    service: SetupService = Depends(get_setup_service),
) -> SetupBootstrapResponse:
    """
    Bootstrap the first business and the first user.

    This is currently intended as a one-time setup action only.
    """
    try:
        return await service.bootstrap(payload)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
