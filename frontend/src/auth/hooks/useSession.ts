import { useQuery } from '@tanstack/react-query';

import { getCurrentSession } from '@/auth/api';
import { ApiError } from '@/shared/lib/api-client';

export function useSession() {
  const query = useQuery({
    queryKey: ['session'],
    queryFn: async () => {
      try {
        return await getCurrentSession();
      } catch (error) {
        if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
          return null;
        }
        throw error;
      }
    },
    retry: false,
    staleTime: 30_000,
  });

  return {
    session: query.data ?? null,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isError: query.isError,
    refetchSession: query.refetch,
  };
}
