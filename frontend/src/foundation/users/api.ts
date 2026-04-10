import { apiRequest } from '@/shared/lib/api-client';
import { env } from '@/shared/lib/env';
import type { Role, ScopeType, UserState } from '@/shared/types/auth';

export interface ManagedUserRecord {
  public_id: string;
  email: string;
  display_name?: string | null;
  state: UserState | string;
  principal_type: string;
}

export interface ManagedMembershipRecord {
  public_id: string;
  role: Role | string;
  scope_type: ScopeType | string;
  scope_id: string;
  user: ManagedUserRecord;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BusinessMembershipsResponse {
  status: 'business_memberships_loaded';
  business: {
    public_id: string;
    name: string;
    status?: string;
  };
  memberships: ManagedMembershipRecord[];
}

export interface CreateBusinessMembershipRequest {
  email: string;
  display_name?: string;
  role: Role | string;
  scope_type?: ScopeType | string;
  scope_public_id?: string;
}

export interface MembershipMutationResponse {
  status: string;
  business: {
    public_id: string;
    name: string;
    status?: string;
  };
  user: ManagedUserRecord;
  membership: ManagedMembershipRecord;
  created_user_shell?: boolean;
}

export interface InviteRecord {
  public_id: string;
  user_public_id: string;
  email: string;
  state: string;
  expires_at: string;
}

export interface InviteMutationResponse {
  status: string;
  next_step: string;
  invite?: InviteRecord;
  invite_token?: string;
  activation_url?: string;
  user: ManagedUserRecord;
  revoked_pending_invite_count?: number;
}

export interface UserLifecycleResponse {
  status: string;
  business: {
    public_id: string;
    name: string;
    status?: string;
  };
  user: ManagedUserRecord;
  revoked_session_count?: number;
  revoked_refresh_token_count?: number;
}

const businessMembershipsUrl = (businessPublicId: string) => `${env.apiBaseUrl}/foundation/businesses/${businessPublicId}/memberships`;
const businessUserActionUrl = (businessPublicId: string, userPublicId: string, action: 'suspend' | 'reactivate') =>
  `${env.apiBaseUrl}/foundation/businesses/${businessPublicId}/users/${userPublicId}/${action}`;
const inviteUrl = (action: 'create' | 'resend' | 'revoke') => `${env.apiBaseUrl}/auth/invites/${action}`;

export async function listBusinessMemberships(businessPublicId: string) {
  return apiRequest<BusinessMembershipsResponse>(businessMembershipsUrl(businessPublicId), { method: 'GET' });
}

export async function createBusinessMembership(businessPublicId: string, payload: CreateBusinessMembershipRequest) {
  return apiRequest<MembershipMutationResponse>(businessMembershipsUrl(businessPublicId), {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function archiveBusinessMembership(businessPublicId: string, membershipPublicId: string) {
  return apiRequest<MembershipMutationResponse>(`${businessMembershipsUrl(businessPublicId)}/${membershipPublicId}`, {
    method: 'DELETE',
  });
}

export async function suspendBusinessUser(businessPublicId: string, userPublicId: string) {
  return apiRequest<UserLifecycleResponse>(businessUserActionUrl(businessPublicId, userPublicId, 'suspend'), { method: 'POST' });
}

export async function reactivateBusinessUser(businessPublicId: string, userPublicId: string) {
  return apiRequest<UserLifecycleResponse>(businessUserActionUrl(businessPublicId, userPublicId, 'reactivate'), { method: 'POST' });
}

export async function createInvite(userPublicId: string) {
  return apiRequest<InviteMutationResponse>(inviteUrl('create'), {
    method: 'POST',
    body: JSON.stringify({ user_public_id: userPublicId }),
  });
}

export async function resendInvite(userPublicId: string) {
  return apiRequest<InviteMutationResponse>(inviteUrl('resend'), {
    method: 'POST',
    body: JSON.stringify({ user_public_id: userPublicId }),
  });
}

export async function revokeInvite(userPublicId: string) {
  return apiRequest<InviteMutationResponse>(inviteUrl('revoke'), {
    method: 'POST',
    body: JSON.stringify({ user_public_id: userPublicId }),
  });
}
