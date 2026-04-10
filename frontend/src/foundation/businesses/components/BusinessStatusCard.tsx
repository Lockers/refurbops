import { Button, Group, Stack, Text } from '@mantine/core';
import { IconArrowRight } from '@tabler/icons-react';
import { Link } from 'react-router-dom';

import { SectionCard } from '@/shared/components/SectionCard';
import { StatusBadge } from '@/shared/components/StatusBadge';

export function BusinessStatusCard({
  id,
  name,
  status,
  subscriptionStatus,
  primarySiteName,
}: {
  id: string;
  name: string;
  status: string;
  subscriptionStatus: string;
  primarySiteName: string;
}) {
  return (
    <SectionCard
      title={name}
      action={<StatusBadge value={status} />}
      description="Business operational state and commercial state must both be obvious."
    >
      <Group justify="space-between" align="center" gap="md" wrap="wrap">
        <Stack gap={4}>
          <Text fw={600}>Primary site</Text>
          <Text c="slate.6" fz="sm">
            {primarySiteName}
          </Text>
        </Stack>
        <Group gap="sm" wrap="wrap">
          <StatusBadge value={subscriptionStatus} />
          <Button component={Link} to={`/app/businesses/${id}`} variant="default" rightSection={<IconArrowRight size={14} />}>
            Open business
          </Button>
        </Group>
      </Group>
    </SectionCard>
  );
}
