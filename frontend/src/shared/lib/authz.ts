
import type { SessionResponse } from '@/shared/types/auth';

type SessionLike = SessionResponse | null | undefined;

function getRoles(session: SessionLike): string[] {
  const roles = (session as { roles?: string[] } | null | undefined)?.roles;
  return Array.isArray(roles) ? roles.filter(Boolean) : [];
}

function getPermissions(session: SessionLike): string[] {
  const permissions = (session as { effective_permissions?: string[] } | null | undefined)?.effective_permissions;
  return Array.isArray(permissions) ? permissions.filter(Boolean) : [];
}

export function getPrincipalType(session: SessionLike): string {
  return session?.user?.principal_type ?? 'tenant_user';
}

export function isPlatformOwner(session: SessionLike): boolean {
  return getPrincipalType(session) === 'platform_owner';
}

export function hasWildcardAccess(session: SessionLike): boolean {
  return getPermissions(session).includes('*');
}

export function hasRole(session: SessionLike, roles: string[]): boolean {
  if (!session) return false;
  if (roles.includes('platform_owner') && isPlatformOwner(session)) return true;

  const sessionRoles = getRoles(session);
  return roles.some((role) => sessionRoles.includes(role));
}

export function hasPermission(session: SessionLike, permission: string): boolean {
  if (!session) return false;
  const permissions = getPermissions(session);

  if (isPlatformOwner(session) || permissions.includes('*') || permissions.includes('all')) {
    return true;
  }

  if (permissions.includes(permission)) {
    return true;
  }

  return permissions.some((granted) => granted.endsWith('*') && permission.startsWith(granted.slice(0, -1)));
}


export function hasAnyPermission(session: SessionLike, permissions: string[]): boolean {
  return permissions.some((permission) => hasPermission(session, permission));
}

export function getPrimaryRole(session: SessionLike): string | null {
  const sessionRoles = getRoles(session);

  if (sessionRoles.length > 0) {
    const order = [
      'platform_owner',
      'organisation_admin',
      'business_owner',
      'business_admin',
      'backmarket_admin',
      'manager',
      'finance_org',
      'finance',
      'technician',
      'qc',
      'viewer',
    ];

    return order.find((role) => sessionRoles.includes(role)) ?? sessionRoles[0] ?? null;
  }

  if (isPlatformOwner(session) || hasWildcardAccess(session)) {
    return 'platform_owner';
  }

  return null;
}

export function getResolvedRoleLabel(session: SessionLike): string {
  return getPrimaryRole(session) ?? 'tenant_user';
}

export function hasAnyMemberships(session: SessionLike): boolean {
  const memberships = (session as { memberships?: unknown[] } | null | undefined)?.memberships;
  return Array.isArray(memberships) && memberships.length > 0;
}

export function canAccessFoundationAdmin(session: SessionLike): boolean {
  return (
    hasRole(session, ['platform_owner', 'organisation_admin', 'business_owner']) ||
    hasAnyPermission(session, ['foundation.*', 'foundation.read', 'foundation.manage', 'business.*', 'tenant.*'])
  );
}

export function canAccessFoundation(session: SessionLike): boolean {
  return canAccessFoundationAdmin(session);
}

export function canManageBusinesses(session: SessionLike): boolean {
  return (
    isPlatformOwner(session) ||
    hasWildcardAccess(session) ||
    hasAnyPermission(session, ['business.*', 'business.read', 'business.manage'])
  );
}

export function canManageUsers(session: SessionLike): boolean {
  return (
    isPlatformOwner(session) ||
    hasWildcardAccess(session) ||
    hasAnyPermission(session, ['users.*', 'users.read', 'users.manage', 'membership.*', 'membership.manage'])
  );
}

export function canManageSubscriptions(session: SessionLike): boolean {
  return (
    isPlatformOwner(session) ||
    hasWildcardAccess(session) ||
    hasAnyPermission(session, ['subscriptions.*', 'subscriptions.read', 'subscriptions.manage'])
  );
}

export function requiresSetupGate(session: SessionLike): boolean {
  if (!session) return false;
  if (isPlatformOwner(session) || hasWildcardAccess(session)) return false;

  const status = (session as { tenant_context?: { business_status?: string | null } } | null | undefined)
    ?.tenant_context?.business_status;

  return Boolean(status);
}

export function isPendingSetup(session: SessionLike): boolean {
  const status = (session as { tenant_context?: { business_status?: string | null } } | null | undefined)
    ?.tenant_context?.business_status;

  return status === 'pending_setup';
}

export function getPrimaryBusinessId(session: SessionLike): string | null {
  return (
    (session as {
      tenant_context?: { primary_business_public_id?: string | null };
    } | null | undefined)?.tenant_context?.primary_business_public_id ?? null
  );
}

export function getDefaultLandingRoute(session: SessionLike): string {
  if (!session) return '/login';

  if (isPlatformOwner(session) || hasWildcardAccess(session)) {
    return '/app/overview';
  }

  if (hasRole(session, ['organisation_admin'])) {
    return '/app/setup';
  }

  if (hasRole(session, ['business_owner'])) {
    const primaryBusiness = getPrimaryBusinessId(session);
    return primaryBusiness ? `/app/businesses/${primaryBusiness}` : '/app/overview';
  }

  return '/app/access-pending';
}
