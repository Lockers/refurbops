import { Alert, Button, Group, Stack, Text, Title } from '@mantine/core';
import { IconAlertTriangle } from '@tabler/icons-react';

export interface BlockedStateProps {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function BlockedState({ title, message, actionLabel, onAction }: BlockedStateProps) {
  return (
    <Alert
      color="red"
      icon={<IconAlertTriangle size={18} />}
      radius="xl"
      variant="light"
      styles={{ root: { border: '1px solid rgba(250, 82, 82, 0.18)' } }}
    >
      <Stack gap="xs">
        <Title order={4}>{title}</Title>
        <Text size="sm">{message}</Text>
        {actionLabel && onAction ? (
          <Group>
            <Button color="red" onClick={onAction} variant="light">
              {actionLabel}
            </Button>
          </Group>
        ) : null}
      </Stack>
    </Alert>
  );
}
