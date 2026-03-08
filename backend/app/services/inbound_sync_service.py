from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.integrations.backmarket.client import BackMarketClient
from app.integrations.backmarket.mapper import BACKMARKET_SOURCE, map_buyback_order_payload
from app.repositories.business_repository import BusinessRepository
from app.repositories.inbound_order_repository import InboundOrderRepository
from app.repositories.sync_state_repository import SyncStateRepository


class InboundSyncService:
    """
    Orchestrates Back Market inbound order synchronization.

    Responsibilities:
    - load business Back Market integration config
    - determine incremental sync window
    - fetch paginated Back Market orders
    - map payloads to internal documents
    - upsert inbound_orders
    - update sync_states
    - Return sync summary
    """

    def __init__(
        self,
        *,
        business_repo: BusinessRepository,
        inbound_repo: InboundOrderRepository,
        sync_state_repo: SyncStateRepository,
        backmarket_client: BackMarketClient,
    ) -> None:
        self._business_repo = business_repo
        self._inbound_repo = inbound_repo
        self._sync_state_repo = sync_state_repo
        self._backmarket_client = backmarket_client

    async def sync_backmarket_buyback(self, business_id: str) -> dict[str, Any]:
        """
        Perform incremental synchronization of Back Market buyback orders.
        """
        started_at = datetime.now(UTC)

        business_config_result = await self._business_repo.get_backmarket_config(business_id)
        if not business_config_result:
            raise RuntimeError("Back Market integration not configured for this business.")

        config = business_config_result.config

        if not config.enabled:
            raise RuntimeError("Back Market integration is disabled for this business.")

        user_agent = self._build_user_agent(config)

        sync_state = await self._sync_state_repo.get_sync_state(business_id, BACKMARKET_SOURCE)

        sync_from = self._calculate_sync_from(sync_state)

        await self._sync_state_repo.record_attempt(
            business_id=business_id,
            source=BACKMARKET_SOURCE,
            attempted_at=started_at,
        )

        fetched = 0
        inserted = 0
        updated = 0

        page = 1

        while True:
            response = await self._backmarket_client.fetch_buyback_orders(
                api_key=config.api_key,
                accept_language=config.accept_language,
                user_agent=user_agent,
                proxy_url=config.proxy_url,
                modification_date_from=sync_from,
                page=page,
            )

            results = response.get("results") or []
            fetched += len(results)

            for payload in results:
                source_reference = payload.get("orderPublicId")

                existing = await self._inbound_repo.get_by_reference(
                    business_id=business_id,
                    source=BACKMARKET_SOURCE,
                    source_reference=source_reference,
                )

                existing_local_state = (existing or {}).get("local_state")

                mapped = map_buyback_order_payload(
                    business_id=business_id,
                    payload=payload,
                    existing_local_state=existing_local_state,
                )

                _, was_inserted = await self._inbound_repo.upsert_order(mapped)

                if was_inserted:
                    inserted += 1
                else:
                    updated += 1

            next_page_url = response.get("next")

            if not next_page_url:
                break

            page += 1

        completed_at = datetime.now(UTC)

        await self._sync_state_repo.record_success(
            business_id=business_id,
            source=BACKMARKET_SOURCE,
            attempted_at=started_at,
            successful_at=completed_at,
        )

        return {
            "business_id": business_id,
            "source": BACKMARKET_SOURCE,
            "fetched": fetched,
            "inserted": inserted,
            "updated": updated,
            "started_at": started_at,
            "completed_at": completed_at,
            "sync_from": sync_from,
        }

    async def get_inbound_queue(
        self,
        *,
        business_id: str,
        filters: dict[str, Any],
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Retrieve inbound queue rows for the business.
        """
        return await self._inbound_repo.list_queue(
            business_id=business_id,
            filters=filters,
            page=page,
            page_size=page_size,
        )

    async def get_inbound_order(
        self,
        *,
        business_id: str,
        inbound_id: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve a single inbound order.
        """
        return await self._inbound_repo.get_by_id(business_id, inbound_id)

    @staticmethod
    def _build_user_agent(config) -> str:
        """
        Build Back Market User-Agent header.

        Format required by Back Market:
        BM-{CompanyName}-{IntegrationName};{contact_email}
        """
        return f"BM-{config.company_name}-{config.integration_name};{config.contact_email}"

    @staticmethod
    def _calculate_sync_from(sync_state: dict | None) -> str | None:
        """
        Determine modificationDate lower bound for incremental sync.

        Uses:
        - last_successful_sync_at - 24h overlap
        """
        if not sync_state:
            return None

        last_success = sync_state.get("last_successful_sync_at")
        if not last_success:
            return None

        if isinstance(last_success, datetime):
            overlap_time = last_success - timedelta(hours=24)
            return overlap_time.isoformat()

        return None
