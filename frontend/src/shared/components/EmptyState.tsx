import { Box, Button, Paper, Stack, Text, ThemeIcon, Title } from '@mantine/core';
import type { ReactNode } from 'react';

export interface EmptyStateProps {
  title: string;
  description: string;
  icon: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ title, description, icon, actionLabel, onAction }: EmptyStateProps) {
  return (
    <Paper
      p="xl"
      radius="xl"
      withBorder
      style={{
        borderStyle: 'dashed',
        borderColor: 'rgba(87, 105, 129, 0.25)',
        background: 'rgba(255,255,255,0.75)',
      }}
    >
      <Stack align="flex-start" gap="lg">
        <ThemeIcon size={52} radius="xl" variant="light" color="brand">
          {icon}
        </ThemeIcon>
        <Box>
          <Title order={3} mb={6}>
            {title}
          </Title>
          <Text c="slate.6" maw={620}>
            {description}
          </Text>
        </Box>
        {actionLabel && onAction ? <Button onClick={onAction}>{actionLabel}</Button> : null}
      </Stack>
    </Paper>
  );
}
