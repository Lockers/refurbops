import {
  IconBuilding,
  IconChartDots3,
  IconChevronRight,
  IconCreditCard,
  IconLayoutDashboard,
  IconSettings,
  IconShieldLock,
  IconUsers,
} from '@tabler/icons-react';
import { Box, Divider, Group, NavLink, Paper, Stack, Text, ThemeIcon } from '@mantine/core';
import { Link, useLocation } from 'react-router-dom';

import { useSession } from '@/auth/hooks/useSession';
import { BrandMark } from '@/shared/components/BrandMark';
import { StatusBadge } from '@/shared/components/StatusBadge';

const primaryItems = [
  { label: 'Overview', href: '/app/overview', icon: IconLayoutDashboard },
  { label: 'Setup hub', href: '/app/setup', icon: IconSettings },
];

const adminItems = [
  { label: 'Businesses', href: '/app/businesses', icon: IconBuilding },
  { label: 'Users', href: '/app/users', icon: IconUsers },
  { label: 'Subscriptions', href: '/app/subscriptions/demo-business', icon: IconCreditCard },
];

export function AppSidebar() {
  const location = useLocation();
  const { session } = useSession();
  const currentBusiness = session?.current_business;

  function isActive(href: string) {
    return location.pathname === href || location.pathname.startsWith(`${href}/`);
  }

  return (
    <Box p="lg" h="100%">
      <Paper
        radius="3xl"
        h="100%"
        p="lg"
        bg="linear-gradient(180deg, #132a63 0%, #0f214d 48%, #0b1737 100%)"
        style={{
          border: '1px solid rgba(255,255,255,0.07)',
          boxShadow: '0 28px 60px rgba(9, 16, 34, 0.34)',
        }}
      >
        <Stack h="100%" gap="lg">
          <BrandMark inverted />

          <Paper
            radius="2xl"
            p="md"
            bg="rgba(255,255,255,0.06)"
            style={{ border: '1px solid rgba(255,255,255,0.08)' }}
          >
            <Stack gap={8}>
              <Text c="rgba(255,255,255,0.58)" fz="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.08em' }}>
                Current organisation
              </Text>
              <Text c="white" fw={800} fz="lg" lh={1.15}>
                {session?.user.principal_type ?? 'Authenticated principal'}
              </Text>
              <Group justify="space-between" gap="sm" align="center">
                <Text c="rgba(255,255,255,0.72)" fz="sm">
                  {session?.user.full_name ?? session?.user.email ?? 'Guest'}
                </Text>
                {currentBusiness?.status ? <StatusBadge value={currentBusiness.status} /> : null}
              </Group>
            </Stack>
          </Paper>

          <Stack gap="xs">
            <Text c="rgba(255,255,255,0.48)" fz="xs" fw={700} tt="uppercase" px="xs" style={{ letterSpacing: '0.08em' }}>
              Workspace
            </Text>
            {primaryItems.map((item) => {
              const active = isActive(item.href);
              return (
                <NavLink
                  key={item.href}
                  active={active}
                  component={Link}
                  to={item.href}
                  label={<Text fw={700}>{item.label}</Text>}
                  leftSection={<item.icon size={18} stroke={1.9} />}
                  rightSection={active ? <IconChevronRight size={16} /> : null}
                  color="brand"
                  styles={{
                    root: {
                      background: active ? 'rgba(255,255,255,0.12)' : 'transparent',
                      color: '#ffffff',
                      border: active ? '1px solid rgba(255,255,255,0.08)' : '1px solid transparent',
                      borderRadius: '12px',
                      transition: 'all 150ms ease',
                    },
                    label: { color: '#ffffff' },
                    section: { color: active ? '#ffffff' : 'rgba(255,255,255,0.68)' },
                  }}
                />
              );
            })}
          </Stack>

          <Stack gap="xs">
            <Text c="rgba(255,255,255,0.48)" fz="xs" fw={700} tt="uppercase" px="xs" style={{ letterSpacing: '0.08em' }}>
              Foundation admin
            </Text>
            {adminItems.map((item) => {
              const active = isActive(item.href);
              return (
                <NavLink
                  key={item.href}
                  active={active}
                  component={Link}
                  to={item.href}
                  label={<Text fw={600}>{item.label}</Text>}
                  leftSection={<item.icon size={18} stroke={1.9} />}
                  color="brand"
                  styles={{
                    root: {
                      background: active ? 'rgba(29, 99, 237, 0.26)' : 'transparent',
                      color: '#ffffff',
                      borderRadius: '12px',
                      transition: 'all 150ms ease',
                    },
                    label: { color: '#ffffff' },
                    section: { color: active ? '#ffffff' : 'rgba(255,255,255,0.68)' },
                  }}
                />
              );
            })}
          </Stack>

          <Divider color="rgba(255,255,255,0.08)" />

          <Paper
            radius="2xl"
            p="md"
            bg="rgba(255,255,255,0.04)"
            style={{ border: '1px solid rgba(255,255,255,0.07)' }}
          >
            <Stack gap="sm">
              <Group gap="sm" wrap="nowrap" align="flex-start">
                <ThemeIcon size={38} radius="xl" variant="light" color="brand">
                  <IconChartDots3 size={18} />
                </ThemeIcon>
                <Stack gap={2}>
                  <Text c="white" fw={700}>Active context</Text>
                  <Text c="rgba(255,255,255,0.68)" fz="sm">
                    Keep organisation, business, and site scope obvious on every screen.
                  </Text>
                </Stack>
              </Group>

              <Box>
                <Text c="rgba(255,255,255,0.48)" fz="xs" fw={700} tt="uppercase" mb={4} style={{ letterSpacing: '0.08em' }}>
                  Business
                </Text>
                <Text c="white" fw={700}>{currentBusiness?.name ?? 'Foundation context not loaded yet'}</Text>
              </Box>

              <Box>
                <Text c="rgba(255,255,255,0.48)" fz="xs" fw={700} tt="uppercase" mb={4} style={{ letterSpacing: '0.08em' }}>
                  Permission model
                </Text>
                <Text c="rgba(255,255,255,0.68)" fz="sm">
                  Backend remains authoritative for tenancy, legality, and write permissions.
                </Text>
              </Box>
            </Stack>
          </Paper>

          <Box mt="auto">
            <Paper
              radius="2xl"
              p="md"
              bg="rgba(255,255,255,0.04)"
              style={{ border: '1px solid rgba(255,255,255,0.07)' }}
            >
              <Group gap="sm" wrap="nowrap" align="flex-start">
                <ThemeIcon size={36} radius="xl" variant="light" color="brand">
                  <IconShieldLock size={17} />
                </ThemeIcon>
                <Stack gap={2}>
                  <Text c="white" fw={700}>Module 00 foundation</Text>
                  <Text c="rgba(255,255,255,0.68)" fz="sm">
                    Auth, setup, business controls, and status-driven admin surfaces first.
                  </Text>
                </Stack>
              </Group>
            </Paper>
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
}

export default AppSidebar;