import { Badge, Group, Paper, Stack, Text } from '@mantine/core';
import { IconBuildingWarehouse, IconMapPin, IconUsersGroup } from '@tabler/icons-react';

import { useSession } from '@/auth/hooks/useSession';

function ContextPill({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <Paper
      radius="xl"
      px="sm"
      py={8}
      withBorder
      bg="white"
      style={{ borderColor: 'rgba(87, 105, 129, 0.14)' }}
    >
      <Group gap={8} wrap="nowrap" align="center">
        {icon}
        <Stack gap={0}>
          <Text fz="10px" c="slate.6" fw={700} tt="uppercase" style={{ letterSpacing: '0.08em' }}>
            {label}
          </Text>
          <Text fz="sm" fw={700} c="ink.8" maw={152} truncate>
            {value}
          </Text>
        </Stack>
      </Group>
    </Paper>
  );
}

export function ContextSwitcher() {
  const { session } = useSession();
  const businessStatus = session?.current_business?.status;

  return (
    <Group gap="sm" wrap="wrap">
      <ContextPill
        label="Principal"
        value={session?.user.principal_type ?? 'No principal loaded'}
        icon={<IconUsersGroup size={16} stroke={1.8} />}
      />
      <ContextPill
        label="Session"
        value={session?.session.public_id ?? 'No active session'}
        icon={<IconBuildingWarehouse size={16} stroke={1.8} />}
      />
      <ContextPill
        label="User"
        value={session?.user.email ?? 'Not signed in'}
        icon={<IconMapPin size={16} stroke={1.8} />}
      />
      {businessStatus ? (
        <Badge variant="light" color={businessStatus === 'read_only' ? 'yellow' : businessStatus === 'suspended' ? 'red' : 'brand'}>
          {businessStatus.replaceAll('_', ' ')}
        </Badge>
      ) : null}
    </Group>
  );
}

export default ContextSwitcher;
