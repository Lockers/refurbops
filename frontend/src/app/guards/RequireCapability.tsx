import type { PropsWithChildren } from 'react';
import { Alert, Center, Stack, Text, Title } from '@mantine/core';
import { useLocation } from 'react-router-dom';

import { useSession } from '@/auth/hooks/useSession';
import { canAccessFoundation, hasWildcardAccess, isPlatformOwner } from '@/shared/lib/authz';

interface RequireCapabilityProps extends PropsWithChildren {
  roles?: string[];
  permission?: string;
  foundation?: boolean;
}

export function RequireCapability({ roles, foundation = false, children }: RequireCapabilityProps) {
  const location = useLocation();
  const { session, isLoading } = useSession();

  if (isLoading) return null;

  let allowed = isPlatformOwner(session) || hasWildcardAccess(session);

  if (!allowed && foundation) {
    allowed = canAccessFoundation(session);
  }

  if (!allowed && roles?.length) {
    const sessionRoles = session?.roles ?? [];
    allowed = roles.some((role) => sessionRoles.includes(role));
  }

  if (allowed) {
    return <>{children}</>;
  }

  return (
    <Center py="xl">
      <Stack maw={560} gap="md">
        <Title order={2}>Access pending</Title>
        <Alert color="yellow" variant="light">
          Your account is signed in, but this area is not enabled for your current access yet.
        </Alert>
        <Text c="dimmed">Requested route: {location.pathname}</Text>
      </Stack>
    </Center>
  );
}

export default RequireCapability;