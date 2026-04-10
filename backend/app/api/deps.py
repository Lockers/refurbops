from __future__ import annotations

from collections.abc import Callable

from fastapi import Request

from app.auth.authorization_service import authorization_service
from app.auth.schemas import AuthenticatedRequestContext
from app.auth.service import auth_service
from app.config import get_settings
from app.db.mongo import get_database


async def require_authenticated_context(request: Request) -> AuthenticatedRequestContext:
    database = await get_database()
    settings = get_settings()
    access_token = request.cookies.get(settings.access_cookie_name)
    return await auth_service.resolve_authenticated_context(
        database=database,
        access_token=access_token,
        correlation_id=getattr(request.state, "correlation_id", None),
    )


async def require_current_user(request: Request) -> dict[str, object]:
    context = await require_authenticated_context(request)
    return context.user


async def require_current_session(request: Request) -> dict[str, object]:
    context = await require_authenticated_context(request)
    return context.session


async def require_platform_owner_context(request: Request) -> AuthenticatedRequestContext:
    context = await require_authenticated_context(request)
    authorization_service.require_platform_owner(context=context)
    return context


def require_permission(permission: str) -> Callable[[Request], AuthenticatedRequestContext]:
    async def dependency(request: Request) -> AuthenticatedRequestContext:
        context = await require_authenticated_context(request)
        authorization_service.require_permission(context=context, permission=permission)
        return context

    return dependency
