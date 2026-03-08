from __future__ import annotations

from app.repositories.business_repository import BusinessRepository
from app.repositories.user_repository import UserRepository
from app.schemas.setup import (
    SetupBootstrapRequest,
    SetupBootstrapResponse,
    SetupStatusResponse,
)


class SetupService:
    """
    Service for first-time system bootstrap.

    Scope:
    - determine whether RefurbOps has already been configured
    - create the first business
    - create the first user
    - store Back Market integration config on the business
    """

    def __init__(
        self,
        *,
        business_repo: BusinessRepository,
        user_repo: UserRepository,
    ) -> None:
        self._business_repo = business_repo
        self._user_repo = user_repo

    async def get_setup_status(self) -> SetupStatusResponse:
        """
        Return whether the system has already been configured.

        Current rule:
        - If at least one business exists, setup is considered complete
        """
        business_count = await self._business_repo.count_businesses()
        return SetupStatusResponse(is_configured=business_count > 0)

    async def bootstrap(self, payload: SetupBootstrapRequest) -> SetupBootstrapResponse:
        """
        Create the first business and first user.

        This endpoint is intentionally one-time only for now.
        """
        existing_business_count = await self._business_repo.count_businesses()
        if existing_business_count > 0:
            raise RuntimeError("System is already configured. Bootstrap is no longer available.")

        business = payload.business
        user = payload.user

        await self._business_repo.create_business(
            business_id=business.id,
            name=business.name,
            vat_registered=business.vat_registered,
            vat_scheme=business.vat_scheme,
            vat_period=business.vat_period,
            vat_period_start=business.vat_period_start,
            backmarket_config=business.backmarket.model_dump(exclude_none=True),
        )

        await self._user_repo.create_user(
            user_id=user.id,
            business_id=business.id,
            name=user.name,
            email=str(user.email),
            role=user.role,
        )

        return SetupBootstrapResponse(
            business_id=business.id,
            user_id=user.id,
            created=True,
        )
