import type { PropsWithChildren } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { useSession } from '@/auth/hooks/useSession';
import { isPendingSetup, requiresSetupGate } from '@/shared/lib/authz';

export function RequireSetup({ children }: PropsWithChildren) {
  const location = useLocation();
  const { session, isLoading } = useSession();

  if (isLoading) return null;

  if (!requiresSetupGate(session)) {
    return <>{children}</>;
  }

  if (isPendingSetup(session) && !location.pathname.startsWith('/app/setup')) {
    return <Navigate to="/app/setup" replace />;
  }

  return <>{children}</>;
}

export default RequireSetup;