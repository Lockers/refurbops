from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import (
    AuthenticatedRequestContext,
    require_authenticated_context,
    require_permission,
)
from app.auth.authorization_service import authorization_service
from app.auth.schemas import (
    AuthorizationProbeResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    MfaEnrollmentCompleteRequest,
    MfaEnrollmentCompleteResponse,
    MfaEnrollmentStartRequest,
    MfaEnrollmentStartResponse,
    ProtectedProbeResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionCurrentResponse,
    SessionLogoutResponse,
    SessionReauthRequest,
    SessionReauthResponse,
    SessionRefreshResponse,
    TenantAuthorizationProbeResponse,
    UserInviteActivateRequest,
    UserInviteActivateResponse,
    UserInviteCreateRequest,
    UserInviteCreateResponse,
    UserInviteResendResponse,
    UserInviteRevokeResponse,
)
from app.auth.service import auth_service
from app.config import get_settings
from app.db.mongo import get_database


auth_router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, *, access_token: str, refresh_token: str, access_max_age: int, refresh_max_age: int) -> None:
    settings = get_settings()
    secure = settings.app_env.lower() != "local"
    response.set_cookie(
        key=settings.access_cookie_name,
        value=access_token,
        max_age=access_max_age,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    secure = settings.app_env.lower() != "local"
    response.delete_cookie(key=settings.access_cookie_name, httponly=True, secure=secure, samesite="lax", path="/")
    response.delete_cookie(key=settings.refresh_cookie_name, httponly=True, secure=secure, samesite="lax", path="/")




@auth_router.post("/invites/create", response_model=UserInviteCreateResponse)
async def create_user_invite(
    payload: UserInviteCreateRequest,
    context: AuthenticatedRequestContext = Depends(require_authenticated_context),
) -> UserInviteCreateResponse:
    database = await get_database()
    return await auth_service.create_user_invite(
        database=database,
        user_public_id=payload.user_public_id,
        actor_context=context,
    )


@auth_router.post("/invites/resend", response_model=UserInviteResendResponse)
async def resend_user_invite(
    payload: UserInviteCreateRequest,
    context: AuthenticatedRequestContext = Depends(require_authenticated_context),
) -> UserInviteResendResponse:
    database = await get_database()
    return await auth_service.resend_user_invite(
        database=database,
        user_public_id=payload.user_public_id,
        actor_context=context,
    )


@auth_router.post("/invites/revoke", response_model=UserInviteRevokeResponse)
async def revoke_user_invite(
    payload: UserInviteCreateRequest,
    context: AuthenticatedRequestContext = Depends(require_authenticated_context),
) -> UserInviteRevokeResponse:
    database = await get_database()
    return await auth_service.revoke_user_invite(
        database=database,
        user_public_id=payload.user_public_id,
        actor_context=context,
    )


@auth_router.post("/invites/activate", response_model=UserInviteActivateResponse)
async def activate_user_invite(payload: UserInviteActivateRequest) -> UserInviteActivateResponse:
    database = await get_database()
    return await auth_service.activate_user_invite(
        database=database,
        invite_token=payload.invite_token,
        password=payload.password,
    )

@auth_router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    database = await get_database()
    return await auth_service.verify_login(database=database, email=payload.email, password=payload.password)


@auth_router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(payload: ChangePasswordRequest) -> ChangePasswordResponse:
    database = await get_database()
    return await auth_service.change_password(
        database=database,
        email=payload.email,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )


@auth_router.post("/mfa/enroll/start", response_model=MfaEnrollmentStartResponse)
async def start_mfa_enrollment(payload: MfaEnrollmentStartRequest) -> MfaEnrollmentStartResponse:
    database = await get_database()
    return await auth_service.start_mfa_enrollment(database=database, email=payload.email, password=payload.password)


@auth_router.post("/mfa/enroll/complete", response_model=MfaEnrollmentCompleteResponse)
async def complete_mfa_enrollment(payload: MfaEnrollmentCompleteRequest) -> MfaEnrollmentCompleteResponse:
    database = await get_database()
    return await auth_service.complete_mfa_enrollment(
        database=database,
        email=payload.email,
        password=payload.password,
        code=payload.code,
    )


@auth_router.post("/session/create", response_model=SessionCreateResponse)
async def create_session(payload: SessionCreateRequest, response: Response) -> SessionCreateResponse:
    database = await get_database()
    session_response, cookie_bundle = await auth_service.create_session(
        database=database,
        email=payload.email,
        password=payload.password,
        code=payload.code,
    )
    _set_auth_cookies(
        response,
        access_token=cookie_bundle.access_token,
        refresh_token=cookie_bundle.refresh_token,
        access_max_age=cookie_bundle.access_max_age_seconds,
        refresh_max_age=cookie_bundle.refresh_max_age_seconds,
    )
    return session_response


@auth_router.get("/session", response_model=SessionCurrentResponse)
async def get_current_session(request: Request) -> SessionCurrentResponse:
    database = await get_database()
    settings = get_settings()
    access_token = request.cookies.get(settings.access_cookie_name)
    return await auth_service.get_current_session(database=database, access_token=access_token)


@auth_router.post("/session/reauth", response_model=SessionReauthResponse)
async def reauthenticate_session(
    payload: SessionReauthRequest,
    context: AuthenticatedRequestContext = Depends(require_authenticated_context),
) -> SessionReauthResponse:
    database = await get_database()
    return await auth_service.reauthenticate_session(
        database=database,
        context=context,
        current_password=payload.current_password,
        code=payload.code,
    )


@auth_router.post("/session/refresh", response_model=SessionRefreshResponse)
async def refresh_session(request: Request, response: Response) -> SessionRefreshResponse:
    database = await get_database()
    settings = get_settings()
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    session_response, cookie_bundle = await auth_service.refresh_session(
        database=database,
        refresh_token=refresh_token,
    )
    _set_auth_cookies(
        response,
        access_token=cookie_bundle.access_token,
        refresh_token=cookie_bundle.refresh_token,
        access_max_age=cookie_bundle.access_max_age_seconds,
        refresh_max_age=cookie_bundle.refresh_max_age_seconds,
    )
    return session_response


@auth_router.post("/logout", response_model=SessionLogoutResponse)
async def logout(request: Request, response: Response) -> SessionLogoutResponse:
    database = await get_database()
    settings = get_settings()
    access_token = request.cookies.get(settings.access_cookie_name)
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    result = await auth_service.logout(
        database=database,
        access_token=access_token,
        refresh_token=refresh_token,
    )
    _clear_auth_cookies(response)
    return result


@auth_router.get("/protected-probe", response_model=ProtectedProbeResponse)
async def protected_probe(
    context: AuthenticatedRequestContext = Depends(require_authenticated_context),
) -> ProtectedProbeResponse:
    return await auth_service.protected_probe(context=context)


@auth_router.get("/authorization-probe", response_model=AuthorizationProbeResponse)
async def authorization_probe(
    context: AuthenticatedRequestContext = Depends(require_permission("platform.system_probe")),
) -> AuthorizationProbeResponse:
    return AuthorizationProbeResponse(
        required_permission="platform.system_probe",
        effective_permissions=authorization_service.list_effective_permissions(context=context),
        user=auth_service._build_user_view(context.user),
        session=auth_service._build_session_view(context.session),
        access_subject=str(context.claims.get("sub", "")),
        access_session_id=str(context.claims.get("sid", "")),
    )


@auth_router.get("/tenant-authorization-probe", response_model=TenantAuthorizationProbeResponse)
async def tenant_authorization_probe(
    context: AuthenticatedRequestContext = Depends(require_permission("tenant.business_owner_probe")),
) -> TenantAuthorizationProbeResponse:
    effective_permissions = authorization_service.list_effective_permissions(context=context)
    return await auth_service.tenant_authorization_probe(
        context=context,
        effective_permissions=effective_permissions,
    )
