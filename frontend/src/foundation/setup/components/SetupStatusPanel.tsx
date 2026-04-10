import { Badge, Group, Paper, Stack, Text, ThemeIcon } from '@mantine/core';
import { IconAlertTriangle, IconArrowRight, IconChecklist, IconProgressAlert } from '@tabler/icons-react';

import { SectionCard } from '@/shared/components/SectionCard';

export function SetupStatusPanel({ issues, nextActions }: { issues: string[]; nextActions: string[] }) {
  return (
    <SectionCard
      title="Control tower"
      description="Make blockers, readiness, and the next safe admin actions obvious at a glance."
      action={
        <Badge color="brand" variant="light" leftSection={<IconChecklist size={12} />}>
          Live view
        </Badge>
      }
    >
      <Stack gap="lg">
        <Paper
          radius="xl"
          p="md"
          bg="rgba(250, 82, 82, 0.05)"
          style={{ border: '1px solid rgba(250, 82, 82, 0.16)' }}
        >
          <Stack gap="sm">
            <Group gap="sm">
              <ThemeIcon size={36} radius="xl" color="red" variant="light">
                <IconProgressAlert size={18} />
              </ThemeIcon>
              <Stack gap={1}>
                <Text fw={700} c="ink.8">
                  Current blockers
                </Text>
                <Text c="slate.6" fz="sm">
                  These states should be impossible to miss before activation or write access.
                </Text>
              </Stack>
            </Group>
            <Stack gap={10}>
              {issues.map((issue) => (
                <Group key={issue} gap={10} wrap="nowrap" align="flex-start">
                  <IconAlertTriangle size={16} color="#fa5252" style={{ marginTop: 2, flexShrink: 0 }} />
                  <Text c="ink.8" fz="sm">
                    {issue}
                  </Text>
                </Group>
              ))}
            </Stack>
          </Stack>
        </Paper>

        <Paper
          radius="xl"
          p="md"
          bg="rgba(29, 99, 237, 0.04)"
          style={{ border: '1px solid rgba(29, 99, 237, 0.12)' }}
        >
          <Stack gap="sm">
            <Text fw={700} c="ink.8">
              Next clean actions
            </Text>
            <Stack gap={10}>
              {nextActions.map((action) => (
                <Group gap={10} key={action} align="flex-start" wrap="nowrap">
                  <ThemeIcon size={24} radius="xl" color="brand" variant="light">
                    <IconArrowRight size={14} />
                  </ThemeIcon>
                  <Text c="slate.7" fz="sm">
                    {action}
                  </Text>
                </Group>
              ))}
            </Stack>
          </Stack>
        </Paper>
      </Stack>
    </SectionCard>
  );
}
