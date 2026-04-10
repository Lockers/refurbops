import {
  ActionIcon,
  Avatar,
  Badge,
  Box,
  Button,
  Group,
  Paper,
  Text,
  TextInput,
  useMantineColorScheme,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconBell, IconLogout, IconMoonStars, IconSearch, IconSparkles, IconSun } from '@tabler/icons-react';
import { useLocation, useNavigate } from 'react-router-dom';

import { ContextSwitcher } from '@/app/shell/ContextSwitcher';
import { logoutCurrentSession } from '@/auth/api';
import { useSession } from '@/auth/hooks/useSession';

const routeMeta: Record<string, { label: string; eyebrow: string }> = {
  '/app/overview': { label: 'Organisation overview', eyebrow: 'Workspace' },
  '/app/setup': { label: 'Setup hub', eyebrow: 'Foundation' },
  '/app/businesses': { label: 'Businesses', eyebrow: 'Foundation admin' },
  '/app/users': { label: 'Users', eyebrow: 'Foundation admin' },
};

export function AppTopbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { session, refetchSession } = useSession();
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  const currentMeta =
    Object.entries(routeMeta).find(([path]) => location.pathname === path || location.pathname.startsWith(`${path}/`))?.[1] ??
    { label: 'RefurbOps', eyebrow: 'Platform' };

  async function handleLogout() {
    try {
      await logoutCurrentSession();
      await refetchSession();
      navigate('/login', { replace: true });
    } catch {
      notifications.show({
        color: 'red',
        title: 'Logout failed',
        message: 'The backend did not accept the logout request.',
      });
    }
  }

  return (
    <Box px="xl" pt="lg">
      <Paper
        radius="3xl"
        px="lg"
        py="md"
        withBorder
        style={{
          background: isDark ? 'rgba(20, 22, 28, 0.92)' : 'rgba(255,255,255,0.88)',
          borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(87, 105, 129, 0.12)',
          backdropFilter: 'blur(18px)',
          boxShadow: isDark ? '0 18px 44px rgba(0,0,0,0.3)' : '0 18px 44px rgba(15, 23, 42, 0.08)',
        }}
      >
        <Group justify="space-between" gap="lg" wrap="wrap">
          <Group gap="lg" wrap="wrap" align="center">
            <Box>
              <Text c="brand.7" fz="xs" fw={700} tt="uppercase" style={{ letterSpacing: '0.08em' }}>
                {currentMeta.eyebrow}
              </Text>
              <Group gap="xs" align="center">
                <Text fw={800} fz="lg" c="ink.8">
                  {currentMeta.label}
                </Text>
                {session?.current_business?.status ? (
                  <Badge variant="dot" color={session.current_business.status === 'read_only' ? 'yellow' : 'brand'}>
                    {session.current_business.status.replaceAll('_', ' ')}
                  </Badge>
                ) : null}
              </Group>
            </Box>

            <TextInput
              placeholder="Search businesses, sites, users, devices"
              leftSection={<IconSearch size={16} />}
              w={340}
              radius="xl"
              styles={{ input: { background: isDark ? 'rgba(255,255,255,0.06)' : '#f7f9fc' } }}
            />

            <ContextSwitcher />
          </Group>

          <Group gap="sm" wrap="nowrap">
            <ActionIcon variant="default" radius="xl" size={42} onClick={toggleColorScheme} title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}>
              {isDark ? <IconSun size={18} /> : <IconMoonStars size={18} />}
            </ActionIcon>
            <ActionIcon variant="default" radius="xl" size={42}>
              <IconBell size={18} />
            </ActionIcon>
            <ActionIcon variant="light" color="brand" radius="xl" size={42}>
              <IconSparkles size={18} />
            </ActionIcon>
            <Group gap="sm" wrap="nowrap" px={6}>
              <Avatar radius="xl" color="brand" variant="light">
                {(session?.user.full_name ?? session?.user.email ?? 'R').slice(0, 1).toUpperCase()}
              </Avatar>
              <Box>
                <Text fw={700} fz="sm">{session?.user.full_name ?? session?.user.email ?? 'No active session'}</Text>
                <Text c="slate.6" fz="xs">{session?.user.email ?? 'Signed out'}</Text>
              </Box>
            </Group>
            <Button leftSection={<IconLogout size={16} />} variant="default" radius="xl" onClick={handleLogout}>
              Logout
            </Button>
          </Group>
        </Group>
      </Paper>
    </Box>
  );
}

export default AppTopbar;