import { useMemo } from 'react';

import { useSession } from '@/auth/hooks/useSession';
import { getResolvedRoleLabel, isPlatformOwner } from '@/shared/lib/authz';

export function useCurrentContext() {
  const { session, isLoading, isError } = useSession();

  return useMemo(() => {
    const tenant = session?.tenant_context ?? {
      organisation_public_ids: [] as string[],
      business_public_ids: [] as string[],
      site_public_ids: [] as string[],
      primary_business_public_id: null as string | null,
      business_status: null as string | null,
    };

    const memberships = session?.memberships ?? [];

    return {
      session,
      isLoading,
      isError,
      resolvedRole: getResolvedRoleLabel(session),
      principalType: session?.user?.principal_type ?? 'tenant_user',
      isPlatformOwner: isPlatformOwner(session),
      membershipCount: memberships.length,
      memberships,
      tenantContext: tenant,
      primaryBusinessPublicId: tenant.primary_business_public_id,
      businessIds: tenant.business_public_ids,
      siteIds: tenant.site_public_ids,
      hasBusinessContext: isPlatformOwner(session) ? true : tenant.business_public_ids.length > 0,
    };
  }, [session, isLoading, isError]);
}