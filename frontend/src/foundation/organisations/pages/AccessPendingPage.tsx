import { Alert, Stack, Text } from '@mantine/core';
import { IconLockAccess } from '@tabler/icons-react';

import { PageHeader } from '@/shared/components/PageHeader';
import { SectionCard } from '@/shared/components/SectionCard';

export function AccessPendingPage() {
  return (
    <Stack gap="lg">
      <PageHeader
        eyebrow="Access"
        title="Access pending"
        description="Your account is authenticated, but this area is not enabled for your current effective permissions yet."
      />

      <SectionCard title="Permission status" description="Once backend permissions are expanded for this role, the matching workspace will become available.">
        <Alert color="yellow" variant="light" radius="lg" icon={<IconLockAccess size={16} />}>
          This workspace requires additional permissions that your current role does not have. Contact your organisation administrator if you believe this is an error.
        </Alert>
        <Text c="slate.6" fz="sm" mt="md">
          Your session is active and valid. The restriction is permission-based, not authentication-based.
        </Text>
      </SectionCard>
    </Stack>
  );
}

export default AccessPendingPage;