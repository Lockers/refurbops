from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


LoginNextStep = Literal[
    "session_issue_ready",
    "password_change_required",
    "mfa_enrollment_required",
    "password_change_and_mfa_enrollment_required",
]

PasswordChangeNextStep = Literal[
    "session_issue_ready",
    "mfa_enrollment_required",
]

MfaEnrollmentStartNextStep = Literal["mfa_verify_code"]
MfaEnrollmentCompleteNextStep = Literal["session_issue_ready"]
SessionCreateNextStep = Literal["authenticated"]
SessionRefreshNextStep = Literal["authenticated"]
SessionLogoutNextStep = Literal["signed_out"]
SessionReauthNextStep = Literal["sensitive_actions_unlocked"]
UserInviteCreateNextStep = Literal["invite_ready"]
UserInviteResendNextStep = Literal["invite_ready"]
UserInviteActivateNextStep = Literal["mfa_enrollment_required", "session_issue_ready"]
UserInviteRevokeNextStep = Literal["invite_revoked"]


@dataclass(slots=True)
class AuthenticatedRequestContext:
    user: dict[str, Any]
    session: dict[str, Any]
    claims: dict[str, Any]
    memberships: list[dict[str, Any]]
    correlation_id: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class ChangePasswordRequest(BaseModel):
    email: EmailStr
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=12)


class MfaEnrollmentStartRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class MfaEnrollmentCompleteRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    code: str = Field(min_length=6, max_length=8)


class SessionCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    code: str = Field(min_length=6, max_length=8)


class SessionReauthRequest(BaseModel):
    current_password: str = Field(min_length=1)
    code: str | None = Field(default=None, min_length=6, max_length=8)


class UserInviteCreateRequest(BaseModel):
    user_public_id: str = Field(min_length=1)


class UserInviteActivateRequest(BaseModel):
    invite_token: str = Field(min_length=1)
    password: str = Field(min_length=12)


class LoginUserView(BaseModel):
    public_id: str
    email: EmailStr
    principal_type: str
    state: str
    password_change_required: bool
    mfa_required: bool


class LoginResponse(BaseModel):
    status: Literal["verified"] = "verified"
    next_step: LoginNextStep
    user: LoginUserView


class ChangePasswordResponse(BaseModel):
    status: Literal["password_changed"] = "password_changed"
    next_step: PasswordChangeNextStep
    user: LoginUserView


class MfaEnrollmentStartResponse(BaseModel):
    status: Literal["mfa_enrollment_started"] = "mfa_enrollment_started"
    next_step: MfaEnrollmentStartNextStep
    user: LoginUserView
    secret: str
    provisioning_uri: str


class MfaEnrollmentCompleteResponse(BaseModel):
    status: Literal["mfa_enrollment_completed"] = "mfa_enrollment_completed"
    next_step: MfaEnrollmentCompleteNextStep
    user: LoginUserView
    recovery_codes: list[str]


class SessionView(BaseModel):
    public_id: str
    created_at: str
    mfa_verified_at: str
    reauthenticated_at: str | None = None
    idle_expires_at: str
    absolute_expires_at: str


class RefreshTokenView(BaseModel):
    public_id: str
    family_id: str
    issued_at: str
    expires_at: str


class SessionCreateResponse(BaseModel):
    status: Literal["session_created"] = "session_created"
    next_step: SessionCreateNextStep
    user: LoginUserView
    session: SessionView
    refresh: RefreshTokenView


class SessionReauthResponse(BaseModel):
    status: Literal["session_reauthenticated"] = "session_reauthenticated"
    next_step: SessionReauthNextStep = "sensitive_actions_unlocked"
    user: LoginUserView
    session: SessionView
    valid_until: str


class UserInviteView(BaseModel):
    public_id: str
    user_public_id: str
    email: EmailStr
    state: str
    expires_at: str


class UserInviteCreateResponse(BaseModel):
    status: Literal["invite_created"] = "invite_created"
    next_step: UserInviteCreateNextStep = "invite_ready"
    invite: UserInviteView
    invite_token: str
    activation_url: str
    user: LoginUserView


class UserInviteActivateResponse(BaseModel):
    status: Literal["invite_accepted"] = "invite_accepted"
    next_step: UserInviteActivateNextStep
    user: LoginUserView


class UserInviteResendResponse(BaseModel):
    status: Literal["invite_resent"] = "invite_resent"
    next_step: UserInviteResendNextStep = "invite_ready"
    invite: UserInviteView
    invite_token: str
    activation_url: str
    user: LoginUserView


class UserInviteRevokeResponse(BaseModel):
    status: Literal["invite_revoked"] = "invite_revoked"
    next_step: UserInviteRevokeNextStep = "invite_revoked"
    user: LoginUserView
    revoked_pending_invite_count: int


class TenantContextSummary(BaseModel):
    organisation_public_ids: list[str]
    business_public_ids: list[str]
    site_public_ids: list[str]
    primary_business_public_id: str | None = None


class SessionCurrentResponse(BaseModel):
    status: Literal["authenticated"] = "authenticated"
    user: LoginUserView
    session: SessionView
    roles: list[str]
    memberships: list[MembershipContextView]
    effective_permissions: list[str]
    tenant_context: TenantContextSummary


class SessionRefreshResponse(BaseModel):
    status: Literal["session_refreshed"] = "session_refreshed"
    next_step: SessionRefreshNextStep
    user: LoginUserView
    session: SessionView
    refresh: RefreshTokenView


class SessionLogoutResponse(BaseModel):
    status: Literal["logged_out"] = "logged_out"
    next_step: SessionLogoutNextStep = "signed_out"


class ProtectedProbeResponse(BaseModel):
    status: Literal["authenticated_request_ok"] = "authenticated_request_ok"
    user: LoginUserView
    session: SessionView
    access_subject: str
    access_session_id: str


class AuthorizationProbeResponse(BaseModel):
    status: Literal["authorized_request_ok"] = "authorized_request_ok"
    required_permission: str
    effective_permissions: list[str]
    user: LoginUserView
    session: SessionView
    access_subject: str
    access_session_id: str


class MembershipContextView(BaseModel):
    public_id: str
    role: str
    scope_type: str
    scope_id: str


class TenantAuthorizationProbeResponse(BaseModel):
    status: Literal["authorized_request_ok"] = "authorized_request_ok"
    required_permission: str
    effective_permissions: list[str]
    memberships: list[MembershipContextView]
    user: LoginUserView
    session: SessionView
    access_subject: str
    access_session_id: str
