import { Alert, Group, Stack, Text } from '@mantine/core';
import { IconLock } from '@tabler/icons-react';

export function ReadOnlyBanner() {
  return (
    <Alert
      color="yellow"
      icon={<IconLock size={18} />}
      mb="lg"
      radius="xl"
      variant="light"
      styles={{ root: { border: '1px solid rgba(250, 176, 5, 0.18)' } }}
    >
      <Group justify="space-between" align="center" gap="md" wrap="wrap">
        <Stack gap={2}>
          <Text fw={700}>This business is currently read only.</Text>
          <Text size="sm">
            Operational write actions should stay visible but blocked until billing or activation is resolved.
          </Text>
        </Stack>
      </Group>
    </Alert>
  );
}
