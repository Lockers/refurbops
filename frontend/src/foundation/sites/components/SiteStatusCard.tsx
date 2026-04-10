import { Stack, Text } from '@mantine/core';

import { SectionCard } from '@/shared/components/SectionCard';
import { StatusBadge } from '@/shared/components/StatusBadge';

export function SiteStatusCard() {
  return (
    <SectionCard title="Site status" action={<StatusBadge value="active" />} description="Site readiness and role-aware visibility.">
      <Stack gap="xs">
        <Text c="slate.7">Primary status: active</Text>
        <Text c="slate.7">Technician and QC access should be scope-aware.</Text>
      </Stack>
    </SectionCard>
  );
}
