import { Button, Group, Stack, Text } from '@mantine/core';
import { IconPlayerPlay, IconRosetteDiscountCheck } from '@tabler/icons-react';

import { SectionCard } from '@/shared/components/SectionCard';

export function BusinessActivationPanel() {
  return (
    <SectionCard
      title="Activation review"
      description="Only organisation admins should be able to explicitly activate a business."
    >
      <Stack gap="md">
        <Text c="slate.7" fz="sm">
          This panel should become the review checkpoint for final readiness, subscription state, and connector health.
        </Text>
        <Group gap="sm">
          <Button variant="default" leftSection={<IconRosetteDiscountCheck size={16} />}>
            Review checks
          </Button>
          <Button leftSection={<IconPlayerPlay size={16} />}>Activate business</Button>
        </Group>
      </Stack>
    </SectionCard>
  );
}
