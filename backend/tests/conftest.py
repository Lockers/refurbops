from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.database import Database

from tests.smoke_helpers import AuthenticatedActor, SmokeSettings, create_authenticated_actor


@pytest.fixture(scope="session")
def smoke_settings() -> SmokeSettings:
    platform_owner_password = os.getenv("SMOKE_PLATFORM_OWNER_PASSWORD", "").strip()
    business_owner_password = os.getenv("SMOKE_BUSINESS_OWNER_PASSWORD", "").strip()
    missing = [
        name
        for name, value in {
            "SMOKE_PLATFORM_OWNER_PASSWORD": platform_owner_password,
            "SMOKE_BUSINESS_OWNER_PASSWORD": business_owner_password,
        }.items()
        if not value
    ]
    if missing:
        pytest.skip(
            "Module 00 smoke tests require env vars: " + ", ".join(sorted(missing))
        )

    return SmokeSettings(
        api_base_url=os.getenv("SMOKE_API_BASE_URL", "http://localhost:8000").rstrip("/"),
        mongo_uri=os.getenv("SMOKE_MONGO_URI", "mongodb://localhost:27017").strip(),
        mongo_db_name=os.getenv("SMOKE_MONGO_DB_NAME", "refurbops").strip(),
        platform_owner_email=os.getenv("SMOKE_PLATFORM_OWNER_EMAIL", "info@repairedtech.co.uk").strip(),
        platform_owner_password=platform_owner_password,
        business_owner_email=os.getenv("SMOKE_BUSINESS_OWNER_EMAIL", "owner-demo@repairedtech.co.uk").strip(),
        business_owner_password=business_owner_password,
    )


@pytest.fixture(scope="session")
def mongo_db(smoke_settings: SmokeSettings) -> Database[Any]:
    client = MongoClient(smoke_settings.mongo_uri, tz_aware=True)
    try:
        yield client[smoke_settings.mongo_db_name]
    finally:
        client.close()


@pytest.fixture()
def platform_owner_session(
    smoke_settings: SmokeSettings,
    mongo_db: Database[Any],
) -> AuthenticatedActor:
    actor = create_authenticated_actor(
        smoke_settings=smoke_settings,
        mongo_db=mongo_db,
        email=smoke_settings.platform_owner_email,
        password=smoke_settings.platform_owner_password,
    )
    try:
        yield actor
    finally:
        actor.client.close()


@pytest.fixture()
def business_owner_session(
    smoke_settings: SmokeSettings,
    mongo_db: Database[Any],
) -> AuthenticatedActor:
    actor = create_authenticated_actor(
        smoke_settings=smoke_settings,
        mongo_db=mongo_db,
        email=smoke_settings.business_owner_email,
        password=smoke_settings.business_owner_password,
    )
    try:
        yield actor
    finally:
        actor.client.close()


@pytest.fixture()
def unique_email() -> str:
    return f"smoke-{uuid4().hex[:10]}@repairedtech.co.uk"
