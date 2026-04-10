import { Button, Group, Stack, Text } from '@mantine/core';

import { SectionCard } from '@/shared/components/SectionCard';
import { StatusBadge } from '@/shared/components/StatusBadge';

export function SubscriptionStatusCard() {
  return (
    <SectionCard
      title="Subscription status"
      description="Business-scoped billing state should surface clearly in admin flows."
      action={<StatusBadge value="past_due" />}
    >
      <Stack gap="sm">
        <Group justify="space-between">
          <Text c="slate.6" fz="sm">
            Plan
          </Text>
          <Text fw={700}>Professional</Text>
        </Group>
        <Group justify="space-between">
          <Text c="slate.6" fz="sm">
            Add-ons
          </Text>
          <Text fw={700}>BM connector · Labels</Text>
        </Group>
        <Button variant="default">Manage billing</Button>
      </Stack>
    </SectionCard>
  );
}
