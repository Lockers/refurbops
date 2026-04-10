import { apiRequest } from '@/shared/lib/api-client';
import { env } from '@/shared/lib/env';
import type {
  ChangePasswordRequest,
  ChangePasswordResponse,
  LoginRequest,
  LoginResponse,
  MfaEnrollmentCompleteRequest,
  MfaEnrollmentCompleteResponse,
  MfaEnrollmentStartRequest,
  MfaEnrollmentStartResponse,
  SessionCreateRequest,
  SessionCreateResponse,
  SessionLogoutResponse,
  SessionReauthRequest,
  SessionReauthResponse,
  SessionRefreshResponse,
  SessionResponse,
} from '@/shared/types/auth';

const authUrl = (path: string) => `${env.apiBaseUrl}/auth${path}`;

export async function getCurrentSession() {
  return apiRequest<SessionResponse>(authUrl('/session'), {
    method: 'GET',
  });
}

export async function login(payload: LoginRequest) {
  return apiRequest<LoginResponse>(authUrl('/login'), {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function changePassword(payload: ChangePasswordRequest) {
  return apiRequest<ChangePasswordResponse>(authUrl('/change-password'), {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function startMfaEnrollment(payload: MfaEnrollmentStartRequest) {
  return apiRequest<MfaEnrollmentStartResponse>(authUrl('/mfa/enroll/start'), {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function completeMfaEnrollment(payload: MfaEnrollmentCompleteRequest) {
  return apiRequest<MfaEnrollmentCompleteResponse>(authUrl('/mfa/enroll/complete'), {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function createSession(payload: SessionCreateRequest) {
  return apiRequest<SessionCreateResponse>(authUrl('/session/create'), {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function reauthenticateSession(payload: SessionReauthRequest | { current_password: string; code?: string }) {
  return apiRequest<SessionReauthResponse>(authUrl('/session/reauth'), {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function refreshSession() {
  return apiRequest<SessionRefreshResponse>(authUrl('/session/refresh'), {
    method: 'POST',
  });
}

export async function logoutCurrentSession() {
  return apiRequest<SessionLogoutResponse>(authUrl('/logout'), {
    method: 'POST',
  });
}

export async function getAuthorizationProbe() {
  return apiRequest<{ allowed: boolean; reason?: string }>(authUrl('/authorization-probe'), {
    method: 'GET',
  });
}

export async function getTenantAuthorizationProbe() {
  return apiRequest<{ allowed: boolean; reason?: string }>(authUrl('/tenant-authorization-probe'), {
    method: 'GET',
  });
}
