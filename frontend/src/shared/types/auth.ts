export type RoleLabel =
  | "platform_owner"
  | "organisation_admin"
  | "business_owner"
  | "business_admin"
  | "manager"
  | "backmarket_admin"
  | "finance"
  | "finance_org"
  | "technician"
  | "qc"
  | "viewer"
  | "tenant_user";

export type Role = RoleLabel;
export type ScopeType = "organisation" | "business" | "site";
export type UserState = "active" | "suspended" | "pending_activation";

export interface SessionUser {
  public_id?: string | null;
  email: string;
  principal_type?: string | null;
  state?: string | null;
  full_name?: string | null;
}

export interface SessionMembership {
  membership_public_id?: string | null;
  role: string;
  organisation_public_id?: string | null;
  business_public_id?: string | null;
  site_public_id?: string | null;
  status?: string | null;
  pending_activation?: boolean;
}

export interface TenantContext {
  organisation_public_ids: string[];
  business_public_ids: string[];
  site_public_ids: string[];
  primary_business_public_id: string | null;
  business_status?: "pending_setup" | "active" | "read_only" | "suspended" | "archived" | null;
  primary_business_name?: string | null;
}

export interface CurrentBusiness {
  public_id?: string | null;
  name?: string | null;
  status?: string | null;
}

export interface SessionRecord {
  public_id?: string | null;
  state?: string | null;
  mfa_state?: string | null;
  last_reauth_at?: string | null;
}

export interface SessionResponse {
  status: string;
  user: SessionUser;
  session: SessionRecord;
  roles: string[];
  memberships: SessionMembership[];
  effective_permissions: string[];
  tenant_context: TenantContext;
  current_business?: CurrentBusiness | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginNextStepUser {
  public_id?: string | null;
  email: string;
  principal_type?: string | null;
  full_name?: string | null;
}

export interface LoginResponse {
  next_step: string;
  user: LoginNextStepUser;
}

export interface ChangePasswordRequest {
  email: string;
  current_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  next_step: string;
  user: LoginNextStepUser;
}

export interface MfaEnrollmentStartRequest {
  email: string;
  password: string;
}

export interface MfaEnrollmentStartResponse {
  secret: string;
  provisioning_uri: string;
  user: LoginNextStepUser;
}

export interface MfaEnrollmentCompleteRequest {
  email: string;
  password: string;
  code: string;
}

export interface MfaEnrollmentCompleteResponse {
  status: string;
}

export interface SessionCreateRequest {
  email: string;
  password: string;
  code?: string;
}

export type SessionCreateResponse = SessionResponse;
export type SessionLogoutResponse = { status: string };
export interface SessionReauthRequest {
  email: string;
  password: string;
}
export type SessionReauthResponse = SessionResponse;
export type SessionRefreshResponse = SessionResponse;