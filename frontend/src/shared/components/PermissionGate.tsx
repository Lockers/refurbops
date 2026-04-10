import type { PropsWithChildren, ReactNode } from 'react';


export interface PermissionGateProps extends PropsWithChildren {
  allowed?: boolean;
  fallback?: ReactNode;
}

export function PermissionGate({ allowed = true, fallback = null, children }: PermissionGateProps) {
  if (!allowed) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
