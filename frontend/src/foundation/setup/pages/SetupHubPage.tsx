import {
  Badge,
  Button,
  Grid,
  Group,
  Paper,
  Progress,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
} from '@mantine/core';
import {
  IconArrowRight,
  IconBuilding,
  IconChecklist,
  IconLockAccess,
  IconPlugConnected,
  IconRocket,
  IconShieldCheck,
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';

import { getSetupHubSummary } from '@/foundation/setup/api';
import { SetupChecklist } from '@/foundation/setup/components/SetupChecklist';
import { SetupStatusPanel } from '@/foundation/setup/components/SetupStatusPanel';
import { KpiTile } from '@/shared/components/KpiTile';
import { PageHeader } from '@/shared/components/PageHeader';
import { SectionCard } from '@/shared/components/SectionCard';
import { StatusBadge } from '@/shared/components/StatusBadge';

export function SetupHubPage() {
  const { data } = useQuery({
    queryKey: ['setup-hub'],
    queryFn: getSetupHubSummary,
  });

  const businesses = data?.businesses ?? [];
  const issueCount = data?.issues.length ?? 0;
  const nextActionCount = data?.next_actions.length ?? 0;
  const readyCount = businesses.filter((business) => business.status === 'active').length;
  const completionPercent = businesses.length > 0 ? Math.round((readyCount / businesses.length) * 100) : 0;

  return (
    <Stack gap="xl">
      <PageHeader
        eyebrow="Setup hub"
        title="Foundation control tower"
        description="Move each business from pending setup into a clean operational state. Status, blockers, connector health, and activation readiness should all be obvious from here."
        actions={
          <Group>
            <Button variant="default" leftSection={<IconPlugConnected size={16} />} radius="xl">
              Connector status
            </Button>
            <Button leftSection={<IconRocket size={16} />} radius="xl">
              Review activation
            </Button>
          </Group>
        }
      />

      <Paper
        radius="3xl"
        p="xl"
        style={{
          background: 'linear-gradient(135deg, #173a8f 0%, #102b66 42%, #0b1c42 100%)',
          color: 'white',
          boxShadow: '0 28px 60px rgba(13, 24, 52, 0.24)',
        }}
      >
        <Grid align="stretch">
          <Grid.Col span={{ base: 12, xl: 7 }}>
            <Stack gap="lg" h="100" justify="space-between">
              <Stack gap="md">
                <Badge color="white" variant="white" c="brand.7" w="fit-content">
                  Module 00 foundation
                </Badge>
                <Text fw={800} fz="2.5rem" lh={1.05} maw={760}>
                  Make setup progress, blockers, and business readiness impossible to miss.
                </Text>
                <Text c="rgba(255,255,255,0.78)" fz="md" maw={700}>
                  This hub is the operational start point for organisation admins. It should show what is ready,
                  what is blocked, and what the next safe action is for each business.
                </Text>
              </Stack>

              <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md">
                <Paper radius="2xl" p="md" bg="rgba(255,255,255,0.08)" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
                  <Stack gap={4}>
                    <Text c="rgba(255,255,255,0.62)" fz="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.08em' }}>
                      Businesses in scope
                    </Text>
                    <Text fw={800} fz="1.85rem">{businesses.length}</Text>
                    <Text c="rgba(255,255,255,0.7)" fz="sm">Organisation-level view across all active setup work.</Text>
                  </Stack>
                </Paper>
                <Paper radius="2xl" p="md" bg="rgba(255,255,255,0.08)" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
                  <Stack gap={4}>
                    <Text c="rgba(255,255,255,0.62)" fz="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.08em' }}>
                      Current blockers
                    </Text>
                    <Text fw={800} fz="1.85rem">{issueCount}</Text>
                    <Text c="rgba(255,255,255,0.7)" fz="sm">Anything that should stop activation or write access.</Text>
                  </Stack>
                </Paper>
                <Paper radius="2xl" p="md" bg="rgba(255,255,255,0.08)" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
                  <Stack gap={4}>
                    <Text c="rgba(255,255,255,0.62)" fz="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.08em' }}>
                      Next actions
                    </Text>
                    <Text fw={800} fz="1.85rem">{nextActionCount}</Text>
                    <Text c="rgba(255,255,255,0.7)" fz="sm">Visible admin tasks that keep setup moving safely.</Text>
                  </Stack>
                </Paper>
              </SimpleGrid>
            </Stack>
          </Grid.Col>

          <Grid.Col span={{ base: 12, xl: 5 }}>
            <Paper radius="2xl" p="xl" bg="rgba(255,255,255,0.96)" c="ink.8" h="100%">
              <Stack gap="lg">
                <Group justify="space-between" align="flex-start">
                  <Stack gap={2}>
                    <Text c="brand.7" fz="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.08em' }}>
                      Setup progress
                    </Text>
                    <Text fw={800} fz="1.5rem" c="ink.8">
                      {completionPercent}% of businesses fully active
                    </Text>
                  </Stack>
                  <ThemeIcon size={42} radius="xl" color="brand" variant="light">
                    <IconShieldCheck size={20} />
                  </ThemeIcon>
                </Group>

                <Progress value={completionPercent} size="lg" radius="xl" color="brand" />

                <Stack gap="sm">
                  <Group justify="space-between">
                    <Text fw={700} c="ink.8">Ready for operation</Text>
                    <Text fw={700} c="ink.8">{readyCount}</Text>
                  </Group>
                  <Group justify="space-between">
                    <Text c="slate.6">Pending activation or setup</Text>
                    <Text c="slate.6">{Math.max(businesses.length - readyCount, 0)}</Text>
                  </Group>
                  <Group justify="space-between">
                    <Text c="slate.6">Blocked by billing or status</Text>
                    <Text c="slate.6">{businesses.filter((business) => business.status === 'read_only' || business.status === 'suspended').length}</Text>
                  </Group>
                </Stack>

                <Paper
                  radius="2xl"
                  p="md"
                  bg="rgba(29, 99, 237, 0.04)"
                  style={{ border: '1px solid rgba(29, 99, 237, 0.12)' }}
                >
                  <Group gap="sm" wrap="nowrap" align="flex-start">
                    <ThemeIcon size={38} radius="xl" color="brand" variant="light">
                      <IconChecklist size={18} />
                    </ThemeIcon>
                    <Stack gap={2}>
                      <Text fw={700} c="ink.8">Admin reminder</Text>
                      <Text c="slate.6" fz="sm">
                        Activation should be explicit. A business must not feel live just because a few records exist.
                      </Text>
                    </Stack>
                  </Group>
                </Paper>
              </Stack>
            </Paper>
          </Grid.Col>
        </Grid>
      </Paper>

      <Grid>
        <Grid.Col span={{ base: 12, md: 6, xl: 3 }}>
          <KpiTile label="Businesses" value={String(data?.organisation.business_count ?? 0)} helper="Across the organisation" tone="brand" icon={<IconBuilding size={18} />} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6, xl: 3 }}>
          <KpiTile label="Pending setup" value={String(businesses.filter((business) => business.status === 'pending_setup').length)} helper="Requires activation review" tone="warning" icon={<IconChecklist size={18} />} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6, xl: 3 }}>
          <KpiTile label="Read only" value={String(businesses.filter((business) => business.status === 'read_only').length)} helper="Blocked until issue is cleared" tone="danger" icon={<IconLockAccess size={18} />} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6, xl: 3 }}>
          <KpiTile label="Next actions" value={String(nextActionCount)} helper="Visible admin tasks" tone="default" icon={<IconArrowRight size={18} />} />
        </Grid.Col>
      </Grid>

      <Grid>
        <Grid.Col span={{ base: 12, xl: 7 }}>
          <SectionCard
            title="Business readiness"
            description="Each business should communicate operational state clearly: pending setup, active, read only, suspended, and subscription health."
            action={
              <Badge color="brand" variant="light">
                {businesses.length} businesses
              </Badge>
            }
          >
            <Stack gap="md">
              {businesses.map((business) => (
                <Paper
                  key={business.id}
                  radius="2xl"
                  p="lg"
                  withBorder
                  style={{ borderColor: 'rgba(87, 105, 129, 0.14)', background: '#ffffff' }}
                >
                  <Stack gap="md">
                    <Group justify="space-between" gap="md" align="flex-start" wrap="wrap">
                      <Stack gap={4}>
                        <Text fw={800} c="ink.8" fz="lg">{business.name}</Text>
                        <Text c="slate.6" fz="sm">Primary site: {business.primary_site_name}</Text>
                      </Stack>
                      <Group gap="sm">
                        <StatusBadge value={business.status} />
                        <StatusBadge value={business.subscription_status} />
                      </Group>
                    </Group>

                    <Grid>
                      <Grid.Col span={{ base: 12, md: 6 }}>
                        <Paper radius="lg" p="md" bg="slate.0">
                          <Stack gap={4}>
                            <Text c="slate.6" fz="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.08em' }}>Setup state</Text>
                            <Text fw={700} c="ink.8">
                              {business.status === 'pending_setup'
                                ? 'Still needs explicit setup completion and activation review.'
                                : business.status === 'read_only'
                                  ? 'Operational views can remain visible, but write actions should be blocked.'
                                  : 'Operationally ready state.'}
                            </Text>
                          </Stack>
                        </Paper>
                      </Grid.Col>
                      <Grid.Col span={{ base: 12, md: 6 }}>
                        <Paper radius="lg" p="md" bg="slate.0">
                          <Stack gap={4}>
                            <Text c="slate.6" fz="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.08em' }}>Commercial state</Text>
                            <Text fw={700} c="ink.8">
                              {business.subscription_status === 'past_due'
                                ? 'Subscription issue is blocking normal access.'
                                : business.subscription_status === 'pending'
                                  ? 'Subscription still needs confirmation before clean activation.'
                                  : 'Subscription state is healthy.'}
                            </Text>
                          </Stack>
                        </Paper>
                      </Grid.Col>
                    </Grid>

                    <Group justify="space-between" align="center" wrap="wrap" gap="md">
                      <Text c="slate.6" fz="sm">Keep navigation available, but make blocked states and required actions obvious.</Text>
                      <Button variant="subtle" rightSection={<IconArrowRight size={14} />}>Open business</Button>
                    </Group>
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </SectionCard>
        </Grid.Col>

        <Grid.Col span={{ base: 12, xl: 5 }}>
          <Stack gap="lg">
            <SetupStatusPanel issues={data?.issues ?? []} nextActions={data?.next_actions ?? []} />
            <SectionCard
              title="Activation checklist"
              description="These checks should read like a controlled release list, not a vague onboarding wizard."
            >
              <SetupChecklist
                items={[
                  { label: 'Business profile confirmed', complete: true },
                  { label: 'First site created and scoped correctly', complete: true },
                  { label: 'Subscription attached and commercially clean', complete: false },
                  { label: 'Connector status reviewed', complete: false },
                  { label: 'Explicit business activation completed', complete: false },
                ]}
              />
            </SectionCard>
          </Stack>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}