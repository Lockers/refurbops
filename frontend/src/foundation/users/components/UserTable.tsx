import { useMemo } from 'react';
import { useMediaQuery } from '@mantine/hooks';
import { Badge, Button, Card, Group, Menu, ScrollArea, Stack, Table, Text } from '@mantine/core';
import { IconDots, IconMailOff, IconMailPlus, IconMailShare, IconPlayerPause, IconReload, IconTrash } from '@tabler/icons-react';

import type { ManagedMembershipRecord } from '@/foundation/users/api';
import { StatusBadge } from '@/shared/components/StatusBadge';

export type InviteUiState =
  | { kind: 'none' }
  | { kind: 'pending'; expiresAt?: string | null }
  | { kind: 'revoked' };

export interface UserTableRow {
  membership: ManagedMembershipRecord;
  inviteState: InviteUiState;
}

interface UserTableProps {
  rows: UserTableRow[];
  loading?: boolean;
  onCreateInvite: (row: UserTableRow) => void;
  onResendInvite: (row: UserTableRow) => void;
  onRevokeInvite: (row: UserTableRow) => void;
  onSuspendUser: (row: UserTableRow) => void;
  onReactivateUser: (row: UserTableRow) => void;
  onArchiveMembership: (row: UserTableRow) => void;
}

function inviteLabel(inviteState: InviteUiState, userState: string) {
  if (userState !== 'pending_activation') return 'Not needed';
  if (inviteState.kind === 'pending') return 'Invite pending';
  if (inviteState.kind === 'revoked') return 'Invite revoked';
  return 'No active invite';
}

function RowActions({
  row,
  onCreateInvite,
  onResendInvite,
  onRevokeInvite,
  onSuspendUser,
  onReactivateUser,
  onArchiveMembership,
}: {
  row: UserTableRow;
  onCreateInvite: (row: UserTableRow) => void;
  onResendInvite: (row: UserTableRow) => void;
  onRevokeInvite: (row: UserTableRow) => void;
  onSuspendUser: (row: UserTableRow) => void;
  onReactivateUser: (row: UserTableRow) => void;
  onArchiveMembership: (row: UserTableRow) => void;
}) {
  const state = row.membership.user.state;
  const archived = Boolean(row.membership.archived_at);
  const showInvite = state === 'pending_activation' && !archived;

  return (
    <Menu shadow="md" withinPortal position="bottom-end">
      <Menu.Target>
        <Button variant="default" size="xs" rightSection={<IconDots size={14} />}>Actions</Button>
      </Menu.Target>
      <Menu.Dropdown>
        {showInvite && row.inviteState.kind !== 'pending' ? (
          <Menu.Item leftSection={<IconMailPlus size={14} />} onClick={() => onCreateInvite(row)}>Create invite</Menu.Item>
        ) : null}
        {showInvite && row.inviteState.kind === 'pending' ? (
          <>
            <Menu.Item leftSection={<IconMailShare size={14} />} onClick={() => onResendInvite(row)}>Resend invite</Menu.Item>
            <Menu.Item leftSection={<IconMailOff size={14} />} onClick={() => onRevokeInvite(row)}>Revoke invite</Menu.Item>
          </>
        ) : null}
        {!archived && state === 'active' ? (
          <Menu.Item leftSection={<IconPlayerPause size={14} />} onClick={() => onSuspendUser(row)}>Suspend user</Menu.Item>
        ) : null}
        {!archived && state === 'suspended' ? (
          <Menu.Item leftSection={<IconReload size={14} />} onClick={() => onReactivateUser(row)}>Reactivate user</Menu.Item>
        ) : null}
        {!archived ? (
          <Menu.Item leftSection={<IconTrash size={14} />} color="red" onClick={() => onArchiveMembership(row)}>Remove access</Menu.Item>
        ) : null}
      </Menu.Dropdown>
    </Menu>
  );
}

export function UserTable({ rows, loading = false, onCreateInvite, onResendInvite, onRevokeInvite, onSuspendUser, onReactivateUser, onArchiveMembership }: UserTableProps) {
  const isMobile = useMediaQuery('(max-width: 48em)');

  const sortedRows = useMemo(() => [...rows].sort((a, b) => {
    if (a.membership.archived_at && !b.membership.archived_at) return 1;
    if (!a.membership.archived_at && b.membership.archived_at) return -1;
    return a.membership.user.email.localeCompare(b.membership.user.email);
  }), [rows]);

  if (loading) {
    return <Text c="slate.6">Loading users…</Text>;
  }

  if (sortedRows.length === 0) {
    return <Text c="slate.6">No memberships exist for this business yet.</Text>;
  }

  if (isMobile) {
    return (
      <Stack gap="sm">
        {sortedRows.map((row) => (
          <Card key={row.membership.public_id} withBorder radius="xl" p="md">
            <Stack gap="sm">
              <Group justify="space-between" align="flex-start">
                <div>
                  <Text fw={700}>{row.membership.user.display_name || row.membership.user.email}</Text>
                  <Text c="slate.6" fz="sm">{row.membership.user.email}</Text>
                </div>
                <RowActions
                  row={row}
                  onCreateInvite={onCreateInvite}
                  onResendInvite={onResendInvite}
                  onRevokeInvite={onRevokeInvite}
                  onSuspendUser={onSuspendUser}
                  onReactivateUser={onReactivateUser}
                  onArchiveMembership={onArchiveMembership}
                />
              </Group>
              <Group gap="xs" wrap="wrap">
                <StatusBadge value={row.membership.archived_at ? 'archived' : row.membership.user.state} />
                <Badge variant="light" color="brand">{String(row.membership.role).replaceAll('_', ' ')}</Badge>
                <Badge variant="outline">{String(row.membership.scope_type)}</Badge>
              </Group>
              <Text c="slate.6" fz="sm">{inviteLabel(row.inviteState, row.membership.user.state)}</Text>
            </Stack>
          </Card>
        ))}
      </Stack>
    );
  }

  return (
    <ScrollArea>
      <Table highlightOnHover verticalSpacing="md" withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>User</Table.Th>
            <Table.Th>Access</Table.Th>
            <Table.Th>Role</Table.Th>
            <Table.Th>Scope</Table.Th>
            <Table.Th>Invite</Table.Th>
            <Table.Th>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {sortedRows.map((row) => (
            <Table.Tr key={row.membership.public_id}>
              <Table.Td>
                <Stack gap={2}>
                  <Text fw={700}>{row.membership.user.display_name || row.membership.user.email}</Text>
                  <Text c="slate.6" fz="sm">{row.membership.user.email}</Text>
                </Stack>
              </Table.Td>
              <Table.Td>
                <StatusBadge value={row.membership.archived_at ? 'archived' : row.membership.user.state} />
              </Table.Td>
              <Table.Td><Text fw={600}>{String(row.membership.role).replaceAll('_', ' ')}</Text></Table.Td>
              <Table.Td>
                <Stack gap={2}>
                  <Text fw={600}>{String(row.membership.scope_type)}</Text>
                  <Text c="slate.6" fz="sm">{row.membership.scope_id}</Text>
                </Stack>
              </Table.Td>
              <Table.Td>
                <Text c="slate.6" fz="sm">{inviteLabel(row.inviteState, row.membership.user.state)}</Text>
                {row.inviteState.kind === 'pending' && row.inviteState.expiresAt ? (
                  <Text c="slate.5" fz="xs">Expires {new Date(row.inviteState.expiresAt).toLocaleString()}</Text>
                ) : null}
              </Table.Td>
              <Table.Td>
                <RowActions
                  row={row}
                  onCreateInvite={onCreateInvite}
                  onResendInvite={onResendInvite}
                  onRevokeInvite={onRevokeInvite}
                  onSuspendUser={onSuspendUser}
                  onReactivateUser={onReactivateUser}
                  onArchiveMembership={onArchiveMembership}
                />
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </ScrollArea>
  );
}
