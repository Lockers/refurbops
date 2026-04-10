import { Group, Paper, Stack, Text, ThemeIcon } from '@mantine/core';
import type { ReactNode } from 'react';

export interface KpiTileProps {
  label: string;
  value: string;
  tone?: 'default' | 'brand' | 'warning' | 'danger' | 'success';
  icon?: ReactNode;
  helper?: string;
}

const toneMap = {
  default: { color: 'slate', bg: 'rgba(87, 105, 129, 0.08)' },
  brand: { color: 'brand', bg: 'rgba(29, 99, 237, 0.10)' },
  warning: { color: 'yellow', bg: 'rgba(250, 176, 5, 0.10)' },
  danger: { color: 'red', bg: 'rgba(250, 82, 82, 0.10)' },
  success: { color: 'green', bg: 'rgba(64, 192, 87, 0.10)' },
} as const;

export function KpiTile({ label, value, helper, tone = 'default', icon }: KpiTileProps) {
  const palette = toneMap[tone];

  return (
    <Paper
      p={{ base: 'md', md: 'lg' }}
      radius="xl"
      withBorder
      style={{
        borderColor: 'rgba(87, 105, 129, 0.16)',
        background: '#ffffff',
        minHeight: '100%',
      }}
    >
      <Group justify="space-between" align="flex-start" gap="sm" wrap="nowrap">
        <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
          <Text c="slate.6" fz="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.06em' }}>
            {label}
          </Text>
          <Text fw={800} fz={{ base: '1.8rem', md: '2rem' }} lh={1.05} c="ink.8" style={{ wordBreak: 'break-word' }}>
            {value}
          </Text>
          {helper ? (
            <Text c="slate.6" fz="sm">
              {helper}
            </Text>
          ) : null}
        </Stack>
        {icon ? (
          <ThemeIcon radius="xl" size={42} variant="light" color={palette.color} style={{ background: palette.bg, flexShrink: 0 }}>
            {icon}
          </ThemeIcon>
        ) : null}
      </Group>
    </Paper>
  );
}
