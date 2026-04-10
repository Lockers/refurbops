import { SimpleGrid, Stack } from '@mantine/core';
import { IconChartBar, IconBuilding, IconLock, IconUsers } from '@tabler/icons-react';

import { PageHeader } from '@/shared/components/PageHeader';
import { KpiTile } from '@/shared/components/KpiTile';
import { SectionCard } from '@/shared/components/SectionCard';
import { useCurrentContext } from '@/shared/hooks/useCurrentContext';

export function OrganisationOverviewPage() {
  const { session, resolvedRole, membershipCount, businessIds } = useCurrentContext();
  const permissionCount = session?.effective_permissions?.length ?? 0;

  return (
    <Stack gap="lg">
      <PageHeader
        eyebrow="Workspace"
        title="Authenticated overview"
        description="Session is live. The shell resolves access from principal type and effective permissions."
      />

      <SimpleGrid cols={{ base: 1, md: 2, xl: 4 }} spacing="md">
        <KpiTile
          label="Resolved role"
          value={resolvedRole.replaceAll('_', ' ')}
          helper="Resolved from session contract"
          tone="brand"
          icon={<IconLock size={20} />}
        />
        <KpiTile
          label="Memberships"
          value={String(membershipCount)}
          helper="Platform owner can validly have zero"
          icon={<IconUsers size={20} />}
        />
        <KpiTile
          label="Businesses in context"
          value={String(businessIds.length)}
          helper="Tenant context may be empty for platform owner"
          icon={<IconBuilding size={20} />}
        />
        <KpiTile
          label="Permissions"
          value={String(permissionCount)}
          helper="Wildcard access is authoritative"
          tone="success"
          icon={<IconChartBar size={20} />}
        />
      </SimpleGrid>

      <SectionCard title="What is true right now" description="Platform owner is a principal type, not a tenant membership role. Empty roles and empty memberships are valid for this account.">
        <Stack gap="sm">
          <Stack gap={4}>
            <strong>Principal type</strong>
            <span>{session?.user?.principal_type ?? '—'}</span>
          </Stack>
        </Stack>
      </SectionCard>
    </Stack>
  );
}

export default OrganisationOverviewPage;