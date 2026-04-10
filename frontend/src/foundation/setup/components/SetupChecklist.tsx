import { Group, Paper, Stack, Text, ThemeIcon } from '@mantine/core';
import { IconCheck, IconChevronRight, IconClockHour4 } from '@tabler/icons-react';

export function SetupChecklist({ items }: { items: { label: string; complete: boolean }[] }) {
  return (
    <Stack gap="sm">
      {items.map((item, index) => (
        <Paper
          key={item.label}
          radius="xl"
          p="md"
          withBorder
          bg={item.complete ? 'rgba(64, 192, 87, 0.04)' : '#ffffff'}
          style={{ borderColor: item.complete ? 'rgba(64, 192, 87, 0.16)' : 'rgba(87, 105, 129, 0.14)' }}
        >
          <Group justify="space-between" gap="md" wrap="nowrap">
            <Group gap="sm" wrap="nowrap" align="flex-start">
              <ThemeIcon color={item.complete ? 'green' : 'brand'} radius="xl" size={32} variant="light">
                {item.complete ? <IconCheck size={16} /> : <IconClockHour4 size={16} />}
              </ThemeIcon>
              <Stack gap={2}>
                <Text fw={700} c="ink.8">
                  {item.label}
                </Text>
                <Text c="slate.6" fz="sm">
                  Step {index + 1} of {items.length}
                </Text>
              </Stack>
            </Group>
            <ThemeIcon variant="subtle" color={item.complete ? 'green' : 'brand'} size={28} radius="xl">
              <IconChevronRight size={16} />
            </ThemeIcon>
          </Group>
        </Paper>
      ))}
    </Stack>
  );
}
