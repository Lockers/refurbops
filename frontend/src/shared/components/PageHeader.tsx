import { Group, Stack, Text, Title } from '@mantine/core';
import type { ReactNode } from 'react';

export interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <Group justify="space-between" align="flex-start" gap="md" wrap="wrap" mb="lg">
      <Stack gap={8} maw={760}>
        {eyebrow ? (
          <Text c="brand.7" fz="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.08em' }}>
            {eyebrow}
          </Text>
        ) : null}
        <Title order={1} fz={{ base: '1.75rem', md: '2.25rem' }}>
          {title}
        </Title>
        {description ? (
          <Text c="slate.6" fz={{ base: 'sm', md: 'md' }} maw={760}>
            {description}
          </Text>
        ) : null}
      </Stack>
      {actions}
    </Group>
  );
}
