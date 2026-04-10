from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
import pyotp
from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.auth.authorization_service import authorization_service
from app.audit.schemas import AuditEventCreate
from app.api.errors import bad_request, conflict, forbidden, internal_error, not_found, unauthorized
from app.audit.service import audit_service
from app.auth.password_service import password_service
from app.auth.repository import AuthRepository
from app.auth.schemas import (
    AuthenticatedRequestContext,
    ChangePasswordResponse,
    LoginResponse,
    LoginUserView,
    MembershipContextView,
    MfaEnrollmentCompleteResponse,
    MfaEnrollmentStartResponse,
    ProtectedProbeResponse,
    RefreshTokenView,
    SessionCreateResponse,
    SessionCurrentResponse,
    SessionReauthResponse,
    TenantContextSummary,
    SessionRefreshResponse,
    SessionLogoutResponse,
    SessionView,
    TenantAuthorizationProbeResponse,
    UserInviteCreateResponse,
    UserInviteResendResponse,
    UserInviteRevokeResponse,
    UserInviteActivateResponse,
    UserInviteView,
)
from app.auth.token_service import token_service
from app.config import get_settings


@dataclass(slots=True)
class SessionCookieBundle:
    access_token: str
    refresh_token: str
    access_max_age_seconds: int
    refresh_max_age_seconds: int


class AuthService:
    def _build_user_view(self, user: dict, *, password_change_required: bool | None = None) -> LoginUserView:
        return LoginUserView(
            public_id=user["public_id"],
            email=user["email"],
            principal_type=user["principal_type"],
            state=user["state"],
            password_change_required=(
                bool(user.get("password_change_required", False))
                if password_change_required is None
                else password_change_required
            ),
            mfa_required=bool(user.get("mfa_required", False)),
        )

    @staticmethod
    def _coerce_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _build_session_view(self, session: dict) -> SessionView:
        reauthenticated_at = session.get("reauthenticated_at")
        return SessionView(
            public_id=session["public_id"],
            created_at=self._coerce_utc(session["created_at"]).isoformat(),
            mfa_verified_at=self._coerce_utc(session["mfa_verified_at"]).isoformat(),
            reauthenticated_at=(self._coerce_utc(reauthenticated_at).isoformat() if reauthenticated_at else None),
            idle_expires_at=self._coerce_utc(session["idle_expires_at"]).isoformat(),
            absolute_expires_at=self._coerce_utc(session["absolute_expires_at"]).isoformat(),
        )

    def _build_refresh_view(self, refresh: dict) -> RefreshTokenView:
        return RefreshTokenView(
            public_id=refresh["public_id"],
            family_id=refresh["family_id"],
            issued_at=self._coerce_utc(refresh["issued_at"]).isoformat(),
            expires_at=self._coerce_utc(refresh["expires_at"]).isoformat(),
        )


    def _build_membership_view(self, membership: dict) -> MembershipContextView:
        return MembershipContextView(
            public_id=membership["public_id"],
            role=membership["role"],
            scope_type=membership["scope_type"],
            scope_id=membership["scope_id"],
        )

    def _build_roles(self, memberships: list[dict]) -> list[str]:
        roles = {str(m.get("role", "")).strip() for m in memberships if str(m.get("role", "")).strip()}
        return sorted(roles)

    @staticmethod
    def _derive_single_business_scope_from_memberships(memberships: list[dict]) -> str | None:
        business_ids = {
            str(m.get("scope_id", "")).strip()
            for m in memberships
            if str(m.get("scope_type", "")).strip() == "business" and str(m.get("scope_id", "")).strip()
        }
        if len(business_ids) == 1:
            return next(iter(business_ids))
        return None

    @staticmethod
    def _derive_single_organisation_scope_from_memberships(memberships: list[dict]) -> str | None:
        organisation_ids = {
            str(m.get("scope_id", "")).strip()
            for m in memberships
            if str(m.get("scope_type", "")).strip() == "organisation" and str(m.get("scope_id", "")).strip()
        }
        if len(organisation_ids) == 1:
            return next(iter(organisation_ids))
        return None

    @staticmethod
    def _derive_single_site_scope_from_memberships(memberships: list[dict]) -> str | None:
        site_ids = {
            str(m.get("scope_id", "")).strip()
            for m in memberships
            if str(m.get("scope_type", "")).strip() == "site" and str(m.get("scope_id", "")).strip()
        }
        if len(site_ids) == 1:
            return next(iter(site_ids))
        return None

    async def _resolve_invite_audit_scope(
        self,
        *,
        repository: AuthRepository,
        actor_context: AuthenticatedRequestContext,
        target_user: dict,
        target_memberships: list[dict],
    ) -> tuple[str | None, str | None, str | None, dict[str, object]]:
        actor_memberships = actor_context.memberships

        actor_organisation_public_id = self._derive_single_organisation_scope_from_memberships(actor_memberships)
        actor_business_public_id = self._derive_single_business_scope_from_memberships(actor_memberships)
        actor_site_public_id = self._derive_single_site_scope_from_memberships(actor_memberships)

        if actor_business_public_id and not actor_organisation_public_id:
            businesses = await repository.get_businesses_by_public_ids(business_public_ids=[actor_business_public_id])
            if businesses:
                actor_organisation_public_id = str(businesses[0].get("organisation_id", "")).strip() or None

        if actor_site_public_id and not actor_business_public_id:
            sites = await repository.get_sites_by_public_ids(site_public_ids=[actor_site_public_id])
            if sites:
                actor_business_public_id = str(sites[0].get("business_id", "")).strip() or None
            if actor_business_public_id and not actor_organisation_public_id:
                businesses = await repository.get_businesses_by_public_ids(business_public_ids=[actor_business_public_id])
                if businesses:
                    actor_organisation_public_id = str(businesses[0].get("organisation_id", "")).strip() or None

        target_organisation_public_id = str(target_user.get("organisation_id", "")).strip() or None
        target_business_public_id = self._derive_single_business_scope_from_memberships(target_memberships)
        target_site_public_id = self._derive_single_site_scope_from_memberships(target_memberships)

        scope_source = "actor" if any([actor_organisation_public_id, actor_business_public_id, actor_site_public_id]) else "target_fallback"

        metadata = {
            "audit_scope_source": scope_source,
            "target_scope_snapshot": {
                "organisation_public_id": target_organisation_public_id,
                "business_public_id": target_business_public_id,
                "site_public_id": target_site_public_id,
                "active_membership_count": len(target_memberships),
            },
        }

        return (
            actor_organisation_public_id or target_organisation_public_id,
            actor_business_public_id or target_business_public_id,
            actor_site_public_id or target_site_public_id,
            metadata,
        )

    async def _build_tenant_context_summary(self, *, repository: AuthRepository, memberships: list[dict]) -> TenantContextSummary:
        organisation_public_ids: set[str] = set()
        business_public_ids: set[str] = set()
        site_public_ids: set[str] = set()

        for membership in memberships:
            scope_type = str(membership.get("scope_type", "")).strip()
            scope_id = str(membership.get("scope_id", "")).strip()
            if not scope_id:
                continue
            if scope_type == "organisation":
                organisation_public_ids.add(scope_id)
            elif scope_type == "business":
                business_public_ids.add(scope_id)
            elif scope_type == "site":
                site_public_ids.add(scope_id)

        direct_site_documents = await repository.get_sites_by_public_ids(site_public_ids=list(site_public_ids))
        for site in direct_site_documents:
            business_id = str(site.get("business_id", "")).strip()
            if business_id:
                business_public_ids.add(business_id)

        business_documents = await repository.get_businesses_by_public_ids(business_public_ids=list(business_public_ids))
        for business in business_documents:
            organisation_id = str(business.get("organisation_id", "")).strip()
            if organisation_id:
                organisation_public_ids.add(organisation_id)

        inherited_site_documents = await repository.get_sites_for_business_ids(business_public_ids=list(business_public_ids))
        for site in inherited_site_documents:
            site_public_id = str(site.get("public_id", "")).strip()
            if site_public_id:
                site_public_ids.add(site_public_id)

        sorted_business_ids = sorted(business_public_ids)
        primary_business_public_id = sorted_business_ids[0] if len(sorted_business_ids) == 1 else None

        return TenantContextSummary(
            organisation_public_ids=sorted(organisation_public_ids),
            business_public_ids=sorted_business_ids,
            site_public_ids=sorted(site_public_ids),
            primary_business_public_id=primary_business_public_id,
        )

    async def _verify_user_password(
        self,
        *,
        database: AsyncDatabase,
        email: str,
        password: str,
    ) -> tuple[AuthRepository, dict, dict]:
        repository = AuthRepository(database)
        user = await repository.get_user_by_email(email=email)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        credentials = await repository.get_credentials_for_user(user_public_id=user["public_id"])
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        if not password_service.verify_password(password, credentials["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        if user.get("state") != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

        return repository, user, credentials

    def _get_sensitive_reauth_anchor(self, session: dict) -> datetime | None:
        for field_name in ("reauthenticated_at", "mfa_verified_at", "created_at"):
            value = session.get(field_name)
            if value:
                return self._coerce_utc(value)
        return None

    def _get_sensitive_reauth_valid_until(self, session: dict) -> datetime | None:
        anchor = self._get_sensitive_reauth_anchor(session)
        if anchor is None:
            return None
        settings = get_settings()
        return anchor + timedelta(minutes=settings.sensitive_reauth_window_minutes)

    async def require_fresh_reauthentication(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        action: str,
    ) -> None:
        _ = database
        valid_until = self._get_sensitive_reauth_valid_until(context.session)
        now = datetime.now(UTC)
        if valid_until and valid_until > now:
            return

        raise forbidden(
            "Fresh reauthentication required",
            reason_code="sensitive_reauth_required",
            context={"action": action},
        )

    async def verify_login(self, *, database: AsyncDatabase, email: str, password: str) -> LoginResponse:
        repository, user, _ = await self._verify_user_password(database=database, email=email, password=password)

        password_change_required = bool(user.get("password_change_required", False))
        mfa_required = bool(user.get("mfa_required", False))
        active_mfa_enrollment = await repository.get_mfa_enrollment_for_user(user_public_id=user["public_id"])
        has_active_mfa = bool(active_mfa_enrollment and active_mfa_enrollment.get("status") == "active")

        if password_change_required and mfa_required and not has_active_mfa:
            next_step = "password_change_and_mfa_enrollment_required"
        elif password_change_required:
            next_step = "password_change_required"
        elif mfa_required and not has_active_mfa:
            next_step = "mfa_enrollment_required"
        else:
            next_step = "session_issue_ready"

        return LoginResponse(next_step=next_step, user=self._build_user_view(user))

    async def change_password(
        self,
        *,
        database: AsyncDatabase,
        email: str,
        current_password: str,
        new_password: str,
    ) -> ChangePasswordResponse:
        repository, user, _ = await self._verify_user_password(
            database=database,
            email=email,
            password=current_password,
        )

        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        new_password_hash = password_service.hash_password(new_password)
        await repository.update_local_password_credentials(
            user_public_id=user["public_id"],
            password_hash=new_password_hash,
        )
        await repository.clear_password_change_required(user_public_id=user["public_id"])

        mfa_required = bool(user.get("mfa_required", False))
        next_step = "mfa_enrollment_required" if mfa_required else "session_issue_ready"

        return ChangePasswordResponse(
            next_step=next_step,
            user=self._build_user_view(user, password_change_required=False),
        )

    async def start_mfa_enrollment(
        self,
        *,
        database: AsyncDatabase,
        email: str,
        password: str,
    ) -> MfaEnrollmentStartResponse:
        repository, user, _ = await self._verify_user_password(
            database=database,
            email=email,
            password=password,
        )

        if not bool(user.get("mfa_required", False)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not required for this user")

        if bool(user.get("password_change_required", False)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change must be completed before MFA enrollment",
            )

        settings = get_settings()
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user["email"], issuer_name=settings.mfa_issuer)

        await repository.start_mfa_enrollment(
            user_public_id=user["public_id"],
            secret=secret,
            provisioning_uri=provisioning_uri,
        )

        return MfaEnrollmentStartResponse(
            next_step="mfa_verify_code",
            user=self._build_user_view(user, password_change_required=False),
            secret=secret,
            provisioning_uri=provisioning_uri,
        )

    async def complete_mfa_enrollment(
        self,
        *,
        database: AsyncDatabase,
        email: str,
        password: str,
        code: str,
    ) -> MfaEnrollmentCompleteResponse:
        repository, user, _ = await self._verify_user_password(
            database=database,
            email=email,
            password=password,
        )

        if not bool(user.get("mfa_required", False)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not required for this user")

        if bool(user.get("password_change_required", False)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change must be completed before MFA enrollment completion",
            )

        enrollment = await repository.get_mfa_enrollment_for_user(user_public_id=user["public_id"])
        if enrollment is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA enrollment has not been started")

        if enrollment.get("status") != "pending_verification":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA enrollment is not pending verification")

        secret = str(enrollment.get("secret", "")).strip()
        if not secret:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="MFA enrollment secret is missing")

        normalized_code = code.replace(" ", "").replace("-", "")
        totp = pyotp.TOTP(secret)
        if not totp.verify(normalized_code, valid_window=1):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

        recovery_codes = [f"{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}" for _ in range(10)]
        recovery_code_hashes = [password_service.hash_password(code_value) for code_value in recovery_codes]

        await repository.complete_mfa_enrollment(user_public_id=user["public_id"])
        await repository.replace_recovery_codes(user_public_id=user["public_id"], code_hashes=recovery_code_hashes)

        return MfaEnrollmentCompleteResponse(
            next_step="session_issue_ready",
            user=self._build_user_view(user, password_change_required=False),
            recovery_codes=recovery_codes,
        )

    async def create_session(
        self,
        *,
        database: AsyncDatabase,
        email: str,
        password: str,
        code: str,
    ) -> tuple[SessionCreateResponse, SessionCookieBundle]:
        repository, user, _ = await self._verify_user_password(database=database, email=email, password=password)

        if bool(user.get("password_change_required", False)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change must be completed before creating a session",
            )

        enrollment = await repository.get_mfa_enrollment_for_user(user_public_id=user["public_id"])
        if enrollment is None or enrollment.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Active MFA enrollment is required before creating a session",
            )

        secret = str(enrollment.get("secret", "")).strip()
        if not secret:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Active MFA secret is missing")

        normalized_code = code.replace(" ", "").replace("-", "")
        totp = pyotp.TOTP(secret)
        if not totp.verify(normalized_code, valid_window=1):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

        settings = get_settings()
        now = datetime.now(UTC)
        access_expires_at = now + timedelta(minutes=settings.access_token_ttl_minutes)
        mfa_verified_at = now
        idle_expires_at = now + timedelta(minutes=settings.session_idle_timeout_minutes)
        absolute_expires_at = now + timedelta(hours=settings.session_absolute_timeout_hours)

        session = await repository.create_auth_session(
            user=user,
            mfa_verified_at=mfa_verified_at,
            idle_expires_at=idle_expires_at,
            absolute_expires_at=absolute_expires_at,
        )

        provisional_refresh = await repository.create_refresh_token_record(
            session_public_id=session["public_id"],
            user_public_id=user["public_id"],
            family_id=session["refresh_family_id"],
            token_hash="pending",
            expires_at=absolute_expires_at,
        )
        refresh_public_id = provisional_refresh["public_id"]
        refresh_token_value, refresh_token_hash = token_service.generate_refresh_token_value(public_id=refresh_public_id)
        await repository.auth_refresh_tokens.update_one(
            {"public_id": refresh_public_id},
            {"$set": {"token_hash": refresh_token_hash, "updated_at": datetime.now(UTC)}},
        )
        refresh = await repository.auth_refresh_tokens.find_one({"public_id": refresh_public_id})
        if refresh is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Refresh token creation failed")

        access_token = token_service.issue_access_token(
            user=user,
            session_public_id=session["public_id"],
            issued_at=now,
            expires_at=access_expires_at,
        )

        response = SessionCreateResponse(
            next_step="authenticated",
            user=self._build_user_view(user, password_change_required=False),
            session=self._build_session_view(session),
            refresh=self._build_refresh_view(refresh),
        )
        cookies = SessionCookieBundle(
            access_token=access_token,
            refresh_token=refresh_token_value,
            access_max_age_seconds=int((access_expires_at - now).total_seconds()),
            refresh_max_age_seconds=int((absolute_expires_at - now).total_seconds()),
        )
        return response, cookies

    async def resolve_authenticated_context(
        self,
        *,
        database: AsyncDatabase,
        access_token: str | None,
        correlation_id: str | None = None,
    ) -> AuthenticatedRequestContext:
        if not access_token:
            raise unauthorized("Missing access token", reason_code="missing_access_token")

        try:
            claims = token_service.decode_access_token(access_token)
        except jwt.InvalidTokenError:
            raise unauthorized("Invalid access token", reason_code="invalid_access_token")

        if claims.get("typ") != "access":
            raise unauthorized("Invalid access token", reason_code="invalid_access_token")

        session_public_id = str(claims.get("sid", "")).strip()
        user_public_id = str(claims.get("sub", "")).strip()
        if not session_public_id or not user_public_id:
            raise unauthorized("Invalid access token", reason_code="invalid_access_token")

        repository = AuthRepository(database)
        session = await repository.get_active_session_by_public_id(session_public_id=session_public_id)
        if session is None:
            raise unauthorized("Session is not active", reason_code="session_revoked")

        now = datetime.now(UTC)
        idle_expires_at = self._coerce_utc(session["idle_expires_at"])
        absolute_expires_at = self._coerce_utc(session["absolute_expires_at"])
        if idle_expires_at <= now or absolute_expires_at <= now:
            raise unauthorized("Session has expired", reason_code="session_expired")

        user = await repository.get_user_by_public_id(user_public_id=user_public_id)
        if user is None or user.get("state") != "active":
            raise unauthorized("User is not active", reason_code="user_not_active")

        if session.get("user_id") != user_public_id:
            raise unauthorized("Session user mismatch", reason_code="session_user_mismatch")

        memberships = await repository.list_active_memberships_for_user(user_public_id=user_public_id)

        await repository.touch_session(session_public_id=session_public_id, last_seen_at=now)
        session["last_seen_at"] = now

        return AuthenticatedRequestContext(user=user, session=session, claims=claims, memberships=memberships, correlation_id=correlation_id)

    async def get_current_session(self, *, database: AsyncDatabase, access_token: str | None) -> SessionCurrentResponse:
        context = await self.resolve_authenticated_context(database=database, access_token=access_token)
        effective_permissions = authorization_service.list_effective_permissions(context=context)
        return SessionCurrentResponse(
            user=self._build_user_view(context.user),
            session=self._build_session_view(context.session),
            roles=self._build_roles(context.memberships),
            memberships=[self._build_membership_view(m) for m in context.memberships],
            effective_permissions=effective_permissions,
            tenant_context=await self._build_tenant_context_summary(repository=AuthRepository(database), memberships=context.memberships),
        )

    async def protected_probe(self, *, context: AuthenticatedRequestContext) -> ProtectedProbeResponse:
        return ProtectedProbeResponse(
            user=self._build_user_view(context.user),
            session=self._build_session_view(context.session),
            access_subject=str(context.claims.get("sub", "")),
            access_session_id=str(context.claims.get("sid", "")),
        )

    async def tenant_authorization_probe(self, *, context: AuthenticatedRequestContext, effective_permissions: list[str]) -> TenantAuthorizationProbeResponse:
        return TenantAuthorizationProbeResponse(
            required_permission="tenant.business_owner_probe",
            effective_permissions=effective_permissions,
            memberships=[self._build_membership_view(m) for m in context.memberships],
            user=self._build_user_view(context.user),
            session=self._build_session_view(context.session),
            access_subject=str(context.claims.get("sub", "")),
            access_session_id=str(context.claims.get("sid", "")),
        )

    async def reauthenticate_session(
        self,
        *,
        database: AsyncDatabase,
        context: AuthenticatedRequestContext,
        current_password: str,
        code: str | None,
    ) -> SessionReauthResponse:
        repository = AuthRepository(database)
        user_public_id = str(context.user.get("public_id", "")).strip()
        if not user_public_id:
            raise unauthorized("User is not active", reason_code="user_not_active")
        user = await repository.get_user_by_public_id(user_public_id=user_public_id)
        if user is None or str(user.get("state", "")) != "active":
            raise unauthorized("User is not active", reason_code="user_not_active")

        credentials = await repository.get_credentials_for_user(user_public_id=user_public_id)
        if credentials is None or not password_service.verify_password(current_password, str(credentials.get("password_hash", ""))):
            raise unauthorized("Invalid reauthentication credentials", reason_code="invalid_reauth_credentials")

        session_public_id = str(context.session.get("public_id", "")).strip()
        if not session_public_id:
            raise unauthorized("Session is not active", reason_code="session_revoked")

        enrollment = await repository.get_mfa_enrollment_for_user(user_public_id=user["public_id"])
        has_active_mfa = bool(enrollment and enrollment.get("status") == "active")
        if bool(user.get("mfa_required", False)) and has_active_mfa:
            if not code or not code.strip():
                raise bad_request(
                    "MFA code is required for fresh reauthentication",
                    reason_code="missing_reauth_mfa_code",
                )
            secret = str(enrollment.get("secret", "")).strip()
            if not secret:
                raise internal_error("Active MFA secret is missing", reason_code="active_mfa_secret_missing")
            normalized_code = code.replace(" ", "").replace("-", "")
            totp = pyotp.TOTP(secret)
            if not totp.verify(normalized_code, valid_window=1):
                raise bad_request("Invalid MFA code", reason_code="invalid_reauth_mfa_code")

        reauthenticated_at = datetime.now(UTC)
        await repository.mark_session_reauthenticated(
            session_public_id=session_public_id,
            reauthenticated_at=reauthenticated_at,
        )
        context.session["reauthenticated_at"] = reauthenticated_at
        valid_until = self._get_sensitive_reauth_valid_until(context.session)
        if valid_until is None:
            valid_until = reauthenticated_at

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="auth.session.reauthenticated",
                entity_type="session",
                entity_public_id=session_public_id,
                organisation_public_id=str(user.get("organisation_id", "")).strip() or None,
                actor=audit_service.actor_from_context(context),
                metadata={
                    "valid_until": valid_until.isoformat(),
                    "mfa_step_up_used": bool(user.get("mfa_required", False)) and has_active_mfa,
                },
                created_at=reauthenticated_at,
            ),
        )

        return SessionReauthResponse(
            user=self._build_user_view(user, password_change_required=bool(user.get("password_change_required", False))),
            session=self._build_session_view(context.session),
            valid_until=valid_until.isoformat(),
        )

    async def refresh_session(
        self,
        *,
        database: AsyncDatabase,
        refresh_token: str | None,
    ) -> tuple[SessionRefreshResponse, SessionCookieBundle]:
        if not refresh_token:
            raise unauthorized("Missing refresh token", reason_code="missing_refresh_token")

        refresh_public_id = token_service.extract_refresh_public_id(refresh_token)
        if not refresh_public_id:
            raise unauthorized("Invalid refresh token", reason_code="invalid_refresh_token")

        repository = AuthRepository(database)
        refresh_record = await repository.get_refresh_token_by_public_id(refresh_public_id=refresh_public_id)
        if refresh_record is None:
            raise unauthorized("Invalid refresh token", reason_code="invalid_refresh_token")

        now = datetime.now(UTC)
        expected_hash = token_service.hash_refresh_token_value(refresh_token)
        stored_hash = str(refresh_record.get("token_hash", ""))
        if stored_hash != expected_hash:
            await repository.revoke_refresh_family(family_id=refresh_record["family_id"], revoked_at=now)
            await repository.revoke_session(session_public_id=refresh_record["session_id"], revoked_at=now)
            raise unauthorized("Invalid refresh token", reason_code="invalid_refresh_token")

        if refresh_record.get("state") != "active" or refresh_record.get("revoked_at") is not None:
            await repository.revoke_refresh_family(family_id=refresh_record["family_id"], revoked_at=now)
            await repository.revoke_session(session_public_id=refresh_record["session_id"], revoked_at=now)
            raise unauthorized("Refresh token has been reused or revoked", reason_code="refresh_token_reused_or_revoked")

        if refresh_record.get("consumed_at") is not None:
            await repository.revoke_refresh_family(family_id=refresh_record["family_id"], revoked_at=now)
            await repository.revoke_session(session_public_id=refresh_record["session_id"], revoked_at=now)
            raise unauthorized("Refresh token has been reused or revoked", reason_code="refresh_token_reused_or_revoked")

        refresh_expires_at = self._coerce_utc(refresh_record["expires_at"])
        if refresh_expires_at <= now:
            await repository.revoke_refresh_token(refresh_public_id=refresh_public_id, revoked_at=now)
            raise unauthorized("Refresh token has expired", reason_code="refresh_token_expired")

        session = await repository.get_active_session_by_public_id(session_public_id=refresh_record["session_id"])
        if session is None:
            raise unauthorized("Session is not active", reason_code="session_revoked")

        idle_expires_at = self._coerce_utc(session["idle_expires_at"])
        absolute_expires_at = self._coerce_utc(session["absolute_expires_at"])
        if idle_expires_at <= now or absolute_expires_at <= now:
            await repository.revoke_refresh_family(family_id=refresh_record["family_id"], revoked_at=now)
            await repository.revoke_session(session_public_id=session["public_id"], revoked_at=now)
            raise unauthorized("Session has expired", reason_code="session_expired")

        user = await repository.get_user_by_public_id(user_public_id=refresh_record["user_id"])
        if user is None or user.get("state") != "active":
            await repository.revoke_refresh_family(family_id=refresh_record["family_id"], revoked_at=now)
            await repository.revoke_session(session_public_id=session["public_id"], revoked_at=now)
            raise unauthorized("User is not active", reason_code="user_not_active")

        new_access_expires_at = now + timedelta(minutes=get_settings().access_token_ttl_minutes)
        new_idle_expires_at = now + timedelta(minutes=get_settings().session_idle_timeout_minutes)

        await repository.mark_refresh_token_consumed(refresh_public_id=refresh_public_id, consumed_at=now)
        await repository.refresh_session_idle_timeout(
            session_public_id=session["public_id"],
            last_seen_at=now,
            idle_expires_at=new_idle_expires_at,
        )
        session["last_seen_at"] = now
        session["idle_expires_at"] = new_idle_expires_at

        new_refresh = await repository.create_refresh_token_record(
            session_public_id=session["public_id"],
            user_public_id=user["public_id"],
            family_id=session["refresh_family_id"],
            token_hash="pending",
            expires_at=absolute_expires_at,
        )
        new_refresh_public_id = new_refresh["public_id"]
        new_refresh_token_value, new_refresh_hash = token_service.generate_refresh_token_value(public_id=new_refresh_public_id)
        await repository.auth_refresh_tokens.update_one(
            {"public_id": new_refresh_public_id},
            {"$set": {"token_hash": new_refresh_hash, "updated_at": datetime.now(UTC)}},
        )
        new_refresh = await repository.get_refresh_token_by_public_id(refresh_public_id=new_refresh_public_id)
        if new_refresh is None:
            raise internal_error("Refresh token rotation failed", reason_code="refresh_rotation_failed")

        access_token = token_service.issue_access_token(
            user=user,
            session_public_id=session["public_id"],
            issued_at=now,
            expires_at=new_access_expires_at,
        )

        response = SessionRefreshResponse(
            next_step="authenticated",
            user=self._build_user_view(user),
            session=self._build_session_view(session),
            refresh=self._build_refresh_view(new_refresh),
        )
        cookies = SessionCookieBundle(
            access_token=access_token,
            refresh_token=new_refresh_token_value,
            access_max_age_seconds=int((new_access_expires_at - now).total_seconds()),
            refresh_max_age_seconds=int((absolute_expires_at - now).total_seconds()),
        )
        return response, cookies


    async def logout(
        self,
        *,
        database: AsyncDatabase,
        access_token: str | None,
        refresh_token: str | None,
    ) -> SessionLogoutResponse:
        repository = AuthRepository(database)
        now = datetime.now(UTC)

        revoked = False

        if refresh_token:
            refresh_public_id = token_service.extract_refresh_public_id(refresh_token)
            if refresh_public_id:
                refresh_record = await repository.get_refresh_token_by_public_id(refresh_public_id=refresh_public_id)
                if refresh_record is not None:
                    family_id = refresh_record.get("family_id")
                    session_id = refresh_record.get("session_id")
                    if family_id:
                        await repository.revoke_refresh_family(family_id=family_id, revoked_at=now)
                        revoked = True
                    if session_id:
                        await repository.revoke_session(session_public_id=session_id, revoked_at=now)
                        revoked = True

        if not revoked and access_token:
            try:
                claims = token_service.decode_access_token(access_token)
            except jwt.InvalidTokenError:
                claims = None

            if claims and claims.get("typ") == "access":
                session_public_id = str(claims.get("sid", "")).strip()
                if session_public_id:
                    session = await repository.get_active_session_by_public_id(session_public_id=session_public_id)
                    if session is not None:
                        family_id = session.get("refresh_family_id")
                        if family_id:
                            await repository.revoke_refresh_family(family_id=family_id, revoked_at=now)
                        await repository.revoke_session(session_public_id=session_public_id, revoked_at=now)

        return SessionLogoutResponse()



    async def _authorize_manage_user_invites(
        self,
        *,
        repository: AuthRepository,
        actor_context: AuthenticatedRequestContext,
        target_user: dict,
        target_memberships: list[dict],
    ) -> None:
        actor_principal_type = str(actor_context.user.get("principal_type", "")).strip()
        if actor_principal_type == "platform_owner":
            return

        if any(str(m.get("role", "")).strip() == "business_owner" for m in target_memberships):
            raise forbidden(
                "Only platform owner can manage invites for business_owner",
                reason_code="admin_role_required",
            )

        authorization_service.require_permission(context=actor_context, permission="membership.manage")

        actor_org_ids: set[str] = {
            str(m.get("scope_id", "")).strip()
            for m in actor_context.memberships
            if str(m.get("scope_type", "")).strip() == "organisation" and str(m.get("scope_id", "")).strip()
        }
        actor_business_ids = [
            str(m.get("scope_id", "")).strip()
            for m in actor_context.memberships
            if str(m.get("scope_type", "")).strip() == "business" and str(m.get("scope_id", "")).strip()
        ]
        if actor_business_ids:
            actor_businesses = await repository.get_businesses_by_public_ids(business_public_ids=actor_business_ids)
            actor_org_ids.update(
                str(b.get("organisation_id", "")).strip()
                for b in actor_businesses
                if str(b.get("organisation_id", "")).strip()
            )

        target_org_id = str(target_user.get("organisation_id", "")).strip()
        if not target_org_id or target_org_id not in actor_org_ids:
            raise forbidden(
                "You do not have scope to manage invites for this user",
                reason_code="scope_mismatch",
            )

    async def _issue_user_invite(
        self,
        *,
        repository: AuthRepository,
        user: dict,
        issued_by_user_id: str,
        revoke_existing_pending: bool,
    ) -> tuple[dict, str, str]:
        now = datetime.now(UTC)
        settings = get_settings()
        expires_at = now + timedelta(hours=settings.email_token_ttl_invite_hours)

        if revoke_existing_pending:
            await repository.revoke_pending_invites_for_user(user_public_id=user["public_id"], revoked_at=now)

        invite = await repository.create_user_invite(
            user_public_id=user["public_id"],
            email=user["email"],
            organisation_id=user.get("organisation_id"),
            token_hash="pending",
            expires_at=expires_at,
            issued_by_user_id=issued_by_user_id,
        )
        invite_token, token_hash = token_service.generate_opaque_token_value(public_id=invite["public_id"])
        await repository.user_invites.update_one(
            {"public_id": invite["public_id"]},
            {"$set": {"token_hash": token_hash, "updated_at": datetime.now(UTC)}},
        )
        invite = await repository.get_invite_by_public_id(invite_public_id=invite["public_id"])
        if invite is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invite creation failed")

        activation_url = f"{settings.app_public_url.rstrip('/')}/activate-invite?token={invite_token}"
        return invite, invite_token, activation_url

    async def create_user_invite(
        self,
        *,
        database: AsyncDatabase,
        user_public_id: str,
        actor_context: AuthenticatedRequestContext,
    ) -> UserInviteCreateResponse:
        repository = AuthRepository(database)
        await self.require_fresh_reauthentication(
            database=database,
            context=actor_context,
            action="auth.invite.create",
        )
        user = await repository.get_user_by_public_id(user_public_id=user_public_id)
        if user is None:
            raise not_found("User not found", reason_code="user_not_found")

        if user.get("principal_type") != "tenant_user":
            raise bad_request("Invite can only be created for tenant users", reason_code="invalid_target_principal_type")

        if user.get("state") != "pending_activation":
            raise bad_request("User is not pending activation", reason_code="user_state_invalid")

        existing_credentials = await repository.get_credentials_for_user(user_public_id=user_public_id)
        if existing_credentials is not None:
            raise conflict("User already has local credentials", reason_code="credentials_already_exist")

        target_memberships = await repository.list_active_memberships_for_user(user_public_id=user_public_id)
        await self._authorize_manage_user_invites(
            repository=repository,
            actor_context=actor_context,
            target_user=user,
            target_memberships=target_memberships,
        )

        pending_invite = await repository.get_pending_invite_for_user(user_public_id=user_public_id)
        if pending_invite is not None:
            raise conflict("Pending invite already exists", reason_code="pending_invite_exists")

        invite, invite_token, activation_url = await self._issue_user_invite(
            repository=repository,
            user=user,
            issued_by_user_id=actor_context.user["public_id"],
            revoke_existing_pending=False,
        )

        organisation_public_id, business_public_id, site_public_id, scope_metadata = await self._resolve_invite_audit_scope(
            repository=repository,
            actor_context=actor_context,
            target_user=user,
            target_memberships=target_memberships,
        )

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="auth.invite.created",
                entity_type="invite",
                entity_public_id=invite["public_id"],
                organisation_public_id=organisation_public_id,
                business_public_id=business_public_id,
                site_public_id=site_public_id,
                actor=audit_service.actor_from_context(actor_context),
                target_user_public_id=str(user["public_id"]),
                metadata={
                    **scope_metadata,
                    "invite_public_id": invite["public_id"],
                    "email": invite["email"],
                    "expires_at": self._coerce_utc(invite["expires_at"]).isoformat(),
                },
            ),
        )

        return UserInviteCreateResponse(
            invite=UserInviteView(
                public_id=invite["public_id"],
                user_public_id=invite["user_id"],
                email=invite["email"],
                state=invite["state"],
                expires_at=self._coerce_utc(invite["expires_at"]).isoformat(),
            ),
            invite_token=invite_token,
            activation_url=activation_url,
            user=self._build_user_view(user),
        )

    async def resend_user_invite(
        self,
        *,
        database: AsyncDatabase,
        user_public_id: str,
        actor_context: AuthenticatedRequestContext,
    ) -> UserInviteResendResponse:
        repository = AuthRepository(database)
        await self.require_fresh_reauthentication(
            database=database,
            context=actor_context,
            action="auth.invite.resend",
        )
        user = await repository.get_user_by_public_id(user_public_id=user_public_id)
        if user is None:
            raise not_found("User not found", reason_code="user_not_found")

        if user.get("principal_type") != "tenant_user":
            raise bad_request("Invite can only be resent for tenant users", reason_code="invalid_target_principal_type")

        if user.get("state") != "pending_activation":
            raise bad_request("User is not pending activation", reason_code="user_state_invalid")

        existing_credentials = await repository.get_credentials_for_user(user_public_id=user_public_id)
        if existing_credentials is not None:
            raise conflict("User already has local credentials", reason_code="credentials_already_exist")

        target_memberships = await repository.list_active_memberships_for_user(user_public_id=user_public_id)
        await self._authorize_manage_user_invites(
            repository=repository,
            actor_context=actor_context,
            target_user=user,
            target_memberships=target_memberships,
        )

        pending_invite = await repository.get_pending_invite_for_user(user_public_id=user_public_id)
        if pending_invite is None:
            raise not_found("No pending invite to resend", reason_code="pending_invite_not_found")

        invite, invite_token, activation_url = await self._issue_user_invite(
            repository=repository,
            user=user,
            issued_by_user_id=actor_context.user["public_id"],
            revoke_existing_pending=True,
        )

        organisation_public_id, business_public_id, site_public_id, scope_metadata = await self._resolve_invite_audit_scope(
            repository=repository,
            actor_context=actor_context,
            target_user=user,
            target_memberships=target_memberships,
        )

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="auth.invite.resent",
                entity_type="invite",
                entity_public_id=invite["public_id"],
                organisation_public_id=organisation_public_id,
                business_public_id=business_public_id,
                site_public_id=site_public_id,
                actor=audit_service.actor_from_context(actor_context),
                target_user_public_id=str(user["public_id"]),
                metadata={
                    **scope_metadata,
                    "invite_public_id": invite["public_id"],
                    "email": invite["email"],
                    "expires_at": self._coerce_utc(invite["expires_at"]).isoformat(),
                    "replaced_pending_invite": True,
                },
            ),
        )

        return UserInviteResendResponse(
            invite=UserInviteView(
                public_id=invite["public_id"],
                user_public_id=invite["user_id"],
                email=invite["email"],
                state=invite["state"],
                expires_at=self._coerce_utc(invite["expires_at"]).isoformat(),
            ),
            invite_token=invite_token,
            activation_url=activation_url,
            user=self._build_user_view(user),
        )

    async def revoke_user_invite(
        self,
        *,
        database: AsyncDatabase,
        user_public_id: str,
        actor_context: AuthenticatedRequestContext,
    ) -> UserInviteRevokeResponse:
        repository = AuthRepository(database)
        await self.require_fresh_reauthentication(
            database=database,
            context=actor_context,
            action="auth.invite.revoke",
        )
        user = await repository.get_user_by_public_id(user_public_id=user_public_id)
        if user is None:
            raise not_found("User not found", reason_code="user_not_found")

        if user.get("principal_type") != "tenant_user":
            raise bad_request("Invite can only be revoked for tenant users", reason_code="invalid_target_principal_type")

        target_memberships = await repository.list_active_memberships_for_user(user_public_id=user_public_id)
        await self._authorize_manage_user_invites(
            repository=repository,
            actor_context=actor_context,
            target_user=user,
            target_memberships=target_memberships,
        )

        revoked_at = datetime.now(UTC)
        revoked_count = await repository.revoke_pending_invites_for_user(
            user_public_id=user_public_id,
            revoked_at=revoked_at,
        )
        if revoked_count == 0:
            raise not_found("No pending invite to revoke", reason_code="pending_invite_not_found")

        organisation_public_id, business_public_id, site_public_id, scope_metadata = await self._resolve_invite_audit_scope(
            repository=repository,
            actor_context=actor_context,
            target_user=user,
            target_memberships=target_memberships,
        )

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="auth.invite.revoked",
                entity_type="user",
                entity_public_id=str(user["public_id"]),
                organisation_public_id=organisation_public_id,
                business_public_id=business_public_id,
                site_public_id=site_public_id,
                actor=audit_service.actor_from_context(actor_context),
                target_user_public_id=str(user["public_id"]),
                metadata={
                    **scope_metadata,
                    "revoked_pending_invite_count": revoked_count,
                },
                created_at=revoked_at,
            ),
        )

        return UserInviteRevokeResponse(
            user=self._build_user_view(user),
            revoked_pending_invite_count=revoked_count,
        )

    async def activate_user_invite(
        self,
        *,
        database: AsyncDatabase,
        invite_token: str,
        password: str,
    ) -> UserInviteActivateResponse:
        if not invite_token:
            raise bad_request("Invite token is required", reason_code="missing_invite_token")

        invite_public_id = token_service.extract_opaque_public_id(invite_token)
        if not invite_public_id:
            raise bad_request("Invalid invite token", reason_code="invalid_invite_token")

        repository = AuthRepository(database)
        invite = await repository.get_invite_by_public_id(invite_public_id=invite_public_id)
        if invite is None:
            raise bad_request("Invalid invite token", reason_code="invalid_invite_token")

        now = datetime.now(UTC)
        expected_hash = token_service.hash_refresh_token_value(invite_token)
        if str(invite.get("token_hash", "")) != expected_hash:
            raise bad_request("Invalid invite token", reason_code="invalid_invite_token")

        if invite.get("state") != "pending" or invite.get("revoked_at") is not None or invite.get("used_at") is not None:
            raise bad_request("Invite is no longer active", reason_code="invite_not_active")

        if self._coerce_utc(invite["expires_at"]) <= now:
            raise bad_request("Invite has expired", reason_code="invite_expired")

        user = await repository.get_user_by_public_id(user_public_id=invite["user_id"])
        if user is None:
            raise not_found("Invite user not found", reason_code="invite_user_not_found")

        if user.get("state") != "pending_activation":
            raise bad_request("User is not pending activation", reason_code="user_state_invalid")

        existing_credentials = await repository.get_credentials_for_user(user_public_id=user["public_id"])
        if existing_credentials is not None:
            raise conflict("User already has credentials", reason_code="credentials_already_exist")

        target_memberships = await repository.list_active_memberships_for_user(user_public_id=user["public_id"])
        issued_by_user = None
        issued_by_memberships: list[dict] = []
        issued_by_user_id = str(invite.get("issued_by_user_id", "")).strip()
        if issued_by_user_id:
            issued_by_user = await repository.get_user_by_public_id(user_public_id=issued_by_user_id)
            issued_by_memberships = await repository.list_active_memberships_for_user(user_public_id=issued_by_user_id)

        password_hash = password_service.hash_password(password)
        await repository.create_local_password_credentials(user_public_id=user["public_id"], password_hash=password_hash)
        await repository.activate_tenant_user(user_public_id=user["public_id"])
        await repository.accept_user_invite(invite_public_id=invite_public_id, accepted_at=now)

        user = await repository.get_user_by_public_id(user_public_id=user["public_id"])
        if user is None:
            raise internal_error("User activation failed", reason_code="user_activation_failed")

        invite_scope_organisation_public_id = (
            self._derive_single_organisation_scope_from_memberships(issued_by_memberships)
            or (str(issued_by_user.get("organisation_id", "")).strip() if issued_by_user else None)
            or (str(invite.get("organisation_id", "")).strip() or None)
            or (str(user.get("organisation_id", "")).strip() or None)
        )
        invite_scope_business_public_id = self._derive_single_business_scope_from_memberships(issued_by_memberships)
        invite_scope_site_public_id = self._derive_single_site_scope_from_memberships(issued_by_memberships)

        if invite_scope_business_public_id and not invite_scope_organisation_public_id:
            businesses = await repository.get_businesses_by_public_ids(
                business_public_ids=[invite_scope_business_public_id]
            )
            if businesses:
                invite_scope_organisation_public_id = str(businesses[0].get("organisation_id", "")).strip() or None

        if invite_scope_site_public_id and not invite_scope_business_public_id:
            sites = await repository.get_sites_by_public_ids(site_public_ids=[invite_scope_site_public_id])
            if sites:
                invite_scope_business_public_id = str(sites[0].get("business_id", "")).strip() or None
            if invite_scope_business_public_id and not invite_scope_organisation_public_id:
                businesses = await repository.get_businesses_by_public_ids(
                    business_public_ids=[invite_scope_business_public_id]
                )
                if businesses:
                    invite_scope_organisation_public_id = str(businesses[0].get("organisation_id", "")).strip() or None

        next_step = "mfa_enrollment_required" if bool(user.get("mfa_required", False)) else "session_issue_ready"

        await audit_service.record_event(
            database=database,
            event=AuditEventCreate(
                event_type="auth.invite.accepted",
                entity_type="invite",
                entity_public_id=invite_public_id,
                organisation_public_id=invite_scope_organisation_public_id,
                business_public_id=invite_scope_business_public_id,
                site_public_id=invite_scope_site_public_id,
                actor=audit_service.actor_from_user(user),
                target_user_public_id=str(user["public_id"]),
                metadata={
                    "audit_scope_source": "invite_issuer" if issued_by_memberships else "invite_record",
                    "target_scope_snapshot": {
                        "organisation_public_id": str(user.get("organisation_id", "")).strip() or None,
                        "business_public_id": self._derive_single_business_scope_from_memberships(target_memberships),
                        "site_public_id": self._derive_single_site_scope_from_memberships(target_memberships),
                        "active_membership_count": len(target_memberships),
                    },
                    "invite_public_id": invite_public_id,
                    "issued_by_user_id": issued_by_user_id or None,
                    "user_state": str(user.get("state", "")),
                    "next_step": next_step,
                },
                created_at=now,
            ),
        )

        return UserInviteActivateResponse(
            next_step=next_step,
            user=self._build_user_view(user, password_change_required=False),
        )

auth_service = AuthService()
