import { useQuery } from '@tanstack/react-query';

import { getAuthorizationProbe, getTenantAuthorizationProbe } from '@/auth/api';
import { ApiError } from '@/shared/lib/api-client';

export function useAuthorizationProbe(enabled = true) {
  const query = useQuery({
    queryKey: ['authorization-probe'],
    queryFn: async () => {
      try {
        return await getAuthorizationProbe();
      } catch (error) {
        if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
          return null;
        }
        throw error;
      }
    },
    enabled,
    retry: false,
    staleTime: 30_000,
  });

  return {
    authorizationProbe: query.data ?? null,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isError: query.isError,
    refetchAuthorizationProbe: query.refetch,
  };
}

export function useTenantAuthorizationProbe(enabled = true) {
  const query = useQuery({
    queryKey: ['tenant-authorization-probe'],
    queryFn: async () => {
      try {
        return await getTenantAuthorizationProbe();
      } catch (error) {
        if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
          return null;
        }
        throw error;
      }
    },
    enabled,
    retry: false,
    staleTime: 30_000,
  });

  return {
    tenantAuthorizationProbe: query.data ?? null,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isError: query.isError,
    refetchTenantAuthorizationProbe: query.refetch,
  };
}
