import { Card, Divider, Group, Stack, Text } from '@mantine/core';
import type { PropsWithChildren, ReactNode } from 'react';

export interface SectionCardProps extends PropsWithChildren {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function SectionCard({ title, description, action, children }: SectionCardProps) {
  return (
    <Card
      p={{ base: 'lg', md: 'xl' }}
      radius="2xl"
      style={{
        borderColor: 'rgba(87, 105, 129, 0.16)',
        background: 'linear-gradient(180deg, rgba(255,255,255,0.96) 0%, #ffffff 100%)',
      }}
    >
      <Stack gap="md">
        <Group justify="space-between" align="flex-start" gap="md" wrap="wrap">
          <Stack gap={4} maw={720}>
            <Text fw={700} fz="lg" c="ink.8">{title}</Text>
            {description ? (
              <Text c="slate.6" fz="sm" maw={680}>{description}</Text>
            ) : null}
          </Stack>
          {action}
        </Group>
        <Divider color="rgba(87, 105, 129, 0.12)" />
        {children}
      </Stack>
    </Card>
  );
}