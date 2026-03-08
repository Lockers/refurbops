from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING
from bson.errors import InvalidId


class InboundOrderRepository:
    """
    Repository for the `inbound_orders` collection.

    Responsibilities:
    - ensure required MongoDB indexes exist
    - upsert inbound orders using the business/source/source_reference key
    - fetch single inbound orders
    - return queue-shaped rows for API/frontend consumption

    This repository must not contain sync orchestration or HTTP logic.
    """

    COLLECTION_NAME = "inbound_orders"

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._database = database
        self._collection: AsyncIOMotorCollection = database[self.COLLECTION_NAME]

    async def ensure_indexes(self) -> None:
        """
        Create all MongoDB indexes required for Module 01.
        """
        await self._collection.create_index(
            [("business_id", ASCENDING), ("source", ASCENDING), ("source_reference", ASCENDING)],
            unique=True,
            name="uq_business_source_source_reference",
        )
        await self._collection.create_index(
            [("business_id", ASCENDING), ("external_status", ASCENDING)],
            name="idx_business_external_status",
        )
        await self._collection.create_index(
            [("business_id", ASCENDING), ("local_state.device_created", ASCENDING)],
            name="idx_business_device_created",
        )
        await self._collection.create_index(
            [("business_id", ASCENDING), ("local_state.hidden_from_inbound", ASCENDING)],
            name="idx_business_hidden_from_inbound",
        )
        await self._collection.create_index(
            [("business_id", ASCENDING), ("modification_date", ASCENDING)],
            name="idx_business_modification_date",
        )
        await self._collection.create_index(
            [("business_id", ASCENDING), ("tracking.tracking_number", ASCENDING)],
            name="idx_business_tracking_number",
        )

    async def upsert_order(self, order_doc: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """
        Upsert an inbound order and preserve and existing local workflow state.

        Match key:
        - business_id
        - source
        - Source_reference

        Returns:
            (stored_document, was_inserted)
        """
        now = datetime.now(UTC)

        match_filter = {
            "business_id": order_doc["business_id"],
            "source": order_doc["source"],
            "source_reference": order_doc["source_reference"],
        }

        existing = await self._collection.find_one(match_filter)
        existing_local_state = (existing or {}).get("local_state") or {}

        doc_to_store = dict(order_doc)
        doc_to_store["local_state"] = {
            "arrived_clicked": existing_local_state.get("arrived_clicked", False),
            "device_created": existing_local_state.get("device_created", False),
            "linked_device_id": existing_local_state.get("linked_device_id"),
            "hidden_from_inbound": existing_local_state.get("hidden_from_inbound", False),
            "archived": existing_local_state.get("archived", False),
        }
        doc_to_store["updated_at"] = now

        update_doc = {
            "$set": doc_to_store,
            "$setOnInsert": {"created_at": now},
        }

        await self._collection.update_one(match_filter, update_doc, upsert=True)
        stored = await self._collection.find_one(match_filter)

        return stored, existing is None

    async def get_by_id(self, business_id: str, inbound_id: str) -> dict[str, Any] | None:
        """
        Fetch a single inbound order by Mongo `_id`, scoped to business.
        """
        try:
            object_id = ObjectId(inbound_id)
        except (InvalidId, TypeError):
            return None

        return await self._collection.find_one(
            {
                "_id": object_id,
                "business_id": business_id,
            }
        )

    async def get_by_reference(
        self,
        business_id: str,
        source: str,
        source_reference: str,
    ) -> dict[str, Any] | None:
        """
        Fetch a single inbound order by the unique business/source/reference key.
        """
        return await self._collection.find_one(
            {
                "business_id": business_id,
                "source": source,
                "source_reference": source_reference,
            }
        )

    async def list_queue(
        self,
        business_id: str,
        filters: dict[str, Any],
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Return queue rows and total count.

        Default active queue:
        - device_created = false
        - hidden_from_inbound = false

        Supported filters:
        - external_status
        - market
        - has_tracking
        - tracking_status_group
        - likely_arrival_bucket
        - arrived_clicked
        """
        query: dict[str, Any] = {
            "business_id": business_id,
            "local_state.device_created": False,
            "local_state.hidden_from_inbound": False,
        }

        external_status = filters.get("external_status")
        if external_status:
            query["external_status"] = external_status

        market = filters.get("market")
        if market:
            query["market"] = market

        has_tracking = filters.get("has_tracking")
        if has_tracking:
            query["tracking.tracking_number"] = {"$nin": [None, ""]}
        elif has_tracking is False:
            query["$and"] = query.get("$and", [])
            query["$and"].append(
                {
                    "$or": [
                        {"tracking.tracking_number": None},
                        {"tracking.tracking_number": ""},
                        {"tracking.tracking_number": {"$exists": False}},
                    ]
                }
            )

        tracking_status_group = filters.get("tracking_status_group")
        if tracking_status_group:
            query["tracking.status_group"] = tracking_status_group

        likely_arrival_bucket = filters.get("likely_arrival_bucket")
        if likely_arrival_bucket:
            query["tracking.likely_arrival_bucket"] = likely_arrival_bucket

        arrived_clicked = filters.get("arrived_clicked")
        if arrived_clicked is not None:
            query["local_state.arrived_clicked"] = arrived_clicked

        total = await self._collection.count_documents(query)

        skip = max(page - 1, 0) * page_size
        cursor = (
            self._collection.find(query)
            .sort("modification_date", -1)
            .skip(skip)
            .limit(page_size)
        )

        rows: list[dict[str, Any]] = []
        async for doc in cursor:
            rows.append(self._to_queue_row(doc))

        return rows, total

    @staticmethod
    def _to_queue_row(doc: dict[str, Any]) -> dict[str, Any]:
        """
        Flatten a raw inbound document into a queue-friendly DTO shape.
        """
        listing = doc.get("listing") or {}
        customer = doc.get("customer") or {}
        original_price = doc.get("original_price") or {}
        tracking = doc.get("tracking") or {}
        local_state = doc.get("local_state") or {}

        customer_full_name = " ".join(
            part for part in [customer.get("first_name"), customer.get("last_name")] if part
        ).strip() or None

        return {
            "_id": str(doc["_id"]),
            "business_id": doc["business_id"],
            "source": doc["source"],
            "source_reference": doc["source_reference"],
            "external_status": doc.get("external_status"),
            "market": doc.get("market"),
            "listing_title": listing.get("title"),
            "listing_grade": listing.get("grade"),
            "customer_full_name": customer_full_name,
            "original_price_value": original_price.get("value"),
            "original_price_currency": original_price.get("currency"),
            "shipper": tracking.get("shipper"),
            "tracking_number": tracking.get("tracking_number"),
            "tracking_status_group": tracking.get("status_group"),
            "likely_arrival_bucket": tracking.get("likely_arrival_bucket"),
            "shipping_date": doc.get("shipping_date"),
            "modification_date": doc.get("modification_date"),
            "arrived_clicked": local_state.get("arrived_clicked", False),
            "device_created": local_state.get("device_created", False),
            "linked_device_id": local_state.get("linked_device_id"),
            "hidden_from_inbound": local_state.get("hidden_from_inbound", False),
            "last_synced_at": doc.get("last_synced_at"),
        }
