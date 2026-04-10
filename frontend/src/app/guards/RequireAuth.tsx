import type { PropsWithChildren } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { useSession } from '@/auth/hooks/useSession';
import { LoadingScreen } from '@/shared/components/LoadingScreen';

export function RequireAuth({ children }: PropsWithChildren) {
  const location = useLocation();
  const { session, isLoading } = useSession();

  if (isLoading) {
    return <LoadingScreen label="Checking your session" />;
  }

  if (!session) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}
