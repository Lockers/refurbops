import { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Badge, Button, Grid, Group, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCopy, IconMailShare, IconShieldLock, IconUserCheck, IconUserPause, IconUsersGroup } from '@tabler/icons-react';

import { reauthenticateSession } from '@/auth/api';
import { useCurrentContext } from '@/shared/hooks/useCurrentContext';
import { useSession } from '@/auth/hooks/useSession';
import { listBusinessSites } from '@/foundation/sites/api';
import {
  archiveBusinessMembership,
  createBusinessMembership,
  createInvite,
  listBusinessMemberships,
  reactivateBusinessUser,
  resendInvite,
  revokeInvite,
  suspendBusinessUser,
  type InviteMutationResponse,
} from '@/foundation/users/api';
import { ReauthModal, type ReauthValues } from '@/foundation/users/components/ReauthModal';
import { UserInviteForm, type UserInviteFormValues } from '@/foundation/users/components/UserInviteForm';
import { UserTable, type InviteUiState, type UserTableRow } from '@/foundation/users/components/UserTable';
import { KpiTile } from '@/shared/components/KpiTile';
import { PageHeader } from '@/shared/components/PageHeader';
import { SectionCard } from '@/shared/components/SectionCard';
import { normaliseApiError } from '@/shared/lib/api-errors';

function hasPermission(permissions: string[], permission: string) {
  return (
    permissions.includes('*') ||
    permissions.includes(permission) ||
    permissions.includes(`${permission.split('.')[0]}.*`) ||
    permissions.includes('tenant.*')
  );
}

interface LatestInvite {
  userPublicId: string;
  email: string;
  activationUrl?: string;
  expiresAt?: string;
}

export function UserListPage() {
  const queryClient = useQueryClient();
  const { session } = useSession();
  const { primaryBusinessPublicId, session: ctxSession } = useCurrentContext();
  const currentBusinessId = primaryBusinessPublicId ?? '';
  const effectivePermissions = ctxSession?.effective_permissions ?? [];
  const roles = ctxSession?.roles ?? [];
  const [latestInvite, setLatestInvite] = useState<LatestInvite | null>(null);
  const [inviteStateByUserId, setInviteStateByUserId] = useState<Record<string, InviteUiState>>({});
  const [reauthOpened, setReauthOpened] = useState(false);
  const [reauthError, setReauthError] = useState<string | null>(null);
  const [pendingSensitiveAction, setPendingSensitiveAction] = useState<(() => Promise<void>) | null>(null);

  const canReadMemberships = hasPermission(effectivePermissions, 'membership.read');
  const canManageMemberships = hasPermission(effectivePermissions, 'membership.manage');
  const canReadSites = hasPermission(effectivePermissions, 'site.read');
  const canAssignBusinessOwner = roles.includes('platform_owner');

  const membershipsQuery = useQuery({
    queryKey: ['business-memberships', currentBusinessId],
    queryFn: () => listBusinessMemberships(currentBusinessId as string),
    enabled: Boolean(currentBusinessId) && canReadMemberships,
  });

  const sitesQuery = useQuery({
    queryKey: ['business-sites', currentBusinessId],
    queryFn: () => listBusinessSites(currentBusinessId as string),
    enabled: Boolean(currentBusinessId) && canReadSites,
  });

  const refreshMemberships = async () => {
    if (!currentBusinessId) return;
    await queryClient.invalidateQueries({ queryKey: ['business-memberships', currentBusinessId] });
  };

  const runSensitive = async (action: () => Promise<void>) => {
    try {
      await action();
    } catch (error) {
      const apiError = normaliseApiError(error);
      if (apiError.reasonCode === 'sensitive_reauth_required') {
        setPendingSensitiveAction(() => action);
        setReauthError(null);
        setReauthOpened(true);
        return;
      }
      notifications.show({ color: 'red', title: 'Action failed', message: apiError.message });
    }
  };

  const finishReauth = async (values: ReauthValues) => {
    try {
      await reauthenticateSession(values);
      setReauthOpened(false);
      setReauthError(null);
      const retry = pendingSensitiveAction;
      setPendingSensitiveAction(null);
      if (retry) {
        await retry();
      }
    } catch (error) {
      setReauthError(normaliseApiError(error).message);
    }
  };

  const rememberInvite = (response: InviteMutationResponse) => {
    setInviteStateByUserId((current) => ({
      ...current,
      [response.user.public_id]: response.invite
        ? { kind: 'pending', expiresAt: response.invite.expires_at }
        : current[response.user.public_id] ?? { kind: 'none' },
    }));

    if (response.invite) {
      setLatestInvite({
        userPublicId: response.user.public_id,
        email: response.invite.email,
        activationUrl: response.activation_url,
        expiresAt: response.invite.expires_at,
      });
    }
  };

  const handleCreateInviteForUser = async (userPublicId: string) => {
    await runSensitive(async () => {
      const response = await createInvite(userPublicId);
      rememberInvite(response);
      notifications.show({ color: 'green', title: 'Invite ready', message: 'Activation link created successfully.' });
    });
  };

  const handleSubmitUser = async (values: UserInviteFormValues) => {
    if (!currentBusinessId) return;

    await runSensitive(async () => {
      const response = await createBusinessMembership(currentBusinessId, {
        email: values.email,
        display_name: values.display_name,
        role: values.role,
        scope_type: values.scope_type,
        scope_public_id: values.scope_type === 'site' ? values.scope_public_id : undefined,
      });

      await refreshMemberships();

      notifications.show({
        color: 'green',
        title: 'Membership created',
        message:
          response.user.state === 'pending_activation'
            ? 'Access created. Preparing the activation invite next.'
            : 'Access created successfully.',
      });

      if (response.user.state === 'pending_activation') {
        try {
          const inviteResponse = await createInvite(response.user.public_id);
          rememberInvite(inviteResponse);
          notifications.show({ color: 'green', title: 'Invite ready', message: 'Activation link created successfully.' });
        } catch (error) {
          const inviteError = normaliseApiError(error);
          if (inviteError.reasonCode === 'pending_invite_exists') {
            setInviteStateByUserId((current) => ({
              ...current,
              [response.user.public_id]: { kind: 'pending' },
            }));
            notifications.show({
              color: 'yellow',
              title: 'Invite already exists',
              message: 'Membership was created. Resend or revoke the existing invite from the user row.',
            });
            return;
          }
          if (inviteError.reasonCode === 'sensitive_reauth_required') {
            setPendingSensitiveAction(() => async () => {
              const retriedInvite = await createInvite(response.user.public_id);
              rememberInvite(retriedInvite);
            });
            setReauthError(null);
            setReauthOpened(true);
            return;
          }
          notifications.show({ color: 'red', title: 'Invite step failed', message: inviteError.message });
        }
      }
    });
  };

  const rows = useMemo<UserTableRow[]>(() => {
    const memberships = membershipsQuery.data?.memberships ?? [];
    return memberships.map((membership) => ({
      membership,
      inviteState: inviteStateByUserId[membership.user.public_id] ?? { kind: 'none' },
    }));
  }, [inviteStateByUserId, membershipsQuery.data?.memberships]);

  const activeCount = rows.filter((row) => !row.membership.archived_at && row.membership.user.state === 'active').length;
  const pendingCount = rows.filter((row) => !row.membership.archived_at && row.membership.user.state === 'pending_activation').length;
  const suspendedCount = rows.filter((row) => !row.membership.archived_at && row.membership.user.state === 'suspended').length;
  const businessName = membershipsQuery.data?.business.name ?? currentBusinessId ?? 'Current business';

  if (!currentBusinessId) {
    return (
      <Stack gap="xl">
        <PageHeader
          eyebrow="Users"
          title="User lifecycle and invite management"
          description="Choose a business context first. This screen is business-scoped in the live backend contract."
        />
        <SectionCard title="No business selected">
          <Text c="slate.6">Your session does not expose a primary business yet. Open a business first, then return here to manage users and invites.</Text>
        </SectionCard>
      </Stack>
    );
  }

  if (!canReadMemberships) {
    return (
      <Stack gap="xl">
        <PageHeader
          eyebrow="Users"
          title="User lifecycle and invite management"
          description="This area is gated from effective permissions, not raw role labels."
        />
        <Alert color="yellow" variant="light">Your current session does not have membership read access for this business yet.</Alert>
      </Stack>
    );
  }

  return (
    <Stack gap="xl">
      <PageHeader
        eyebrow="Users"
        title="User lifecycle and invite management"
        description="Create memberships first, then continue invite activation only when the user still needs credentials and activation."
        actions={<Badge variant="light" color="brand">{businessName}</Badge>}
      />

      {latestInvite?.activationUrl ? (
        <Alert color="blue" variant="light" icon={<IconMailShare size={16} />}>
          <Group justify="space-between" align="flex-start" gap="md" wrap="wrap">
            <Stack gap={4}>
              <Text fw={700}>Invite ready for {latestInvite.email}</Text>
              <Text c="slate.6" fz="sm">
                Copy the activation link and send it to the user. {latestInvite.expiresAt ? `Expires ${new Date(latestInvite.expiresAt).toLocaleString()}.` : ''}
              </Text>
            </Stack>
            <Button
              size="xs"
              variant="light"
              leftSection={<IconCopy size={14} />}
              onClick={async () => {
                await navigator.clipboard.writeText(latestInvite.activationUrl ?? '');
                notifications.show({ color: 'green', title: 'Copied', message: 'Activation link copied.' });
              }}
            >
              Copy activation link
            </Button>
          </Group>
        </Alert>
      ) : null}

      <Grid>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <KpiTile label="Active users" value={String(activeCount)} helper="Ready to work" tone="success" icon={<IconUserCheck size={18} />} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <KpiTile label="Pending activation" value={String(pendingCount)} helper="Needs invite acceptance" tone="warning" icon={<IconUsersGroup size={18} />} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <KpiTile label="Suspended" value={String(suspendedCount)} helper="Blocked from login" tone="danger" icon={<IconUserPause size={18} />} />
        </Grid.Col>
      </Grid>

      <Grid>
        <Grid.Col span={{ base: 12, xl: 8 }}>
          <SectionCard
            title="Current access"
            description="Each row is a business membership. Pending activation means the shell exists, but the user still needs invite acceptance and credentials before they can sign in."
            action={canManageMemberships ? <Badge variant="dot" color="green">Membership management enabled</Badge> : null}
          >
            <UserTable
              rows={rows}
              loading={membershipsQuery.isLoading}
              onCreateInvite={(row) => void handleCreateInviteForUser(row.membership.user.public_id)}
              onResendInvite={(row) => {
                void runSensitive(async () => {
                  const response = await resendInvite(row.membership.user.public_id);
                  rememberInvite(response);
                  notifications.show({ color: 'green', title: 'Invite resent', message: 'A fresh invite link is ready.' });
                });
              }}
              onRevokeInvite={(row) => {
                void runSensitive(async () => {
                  const response = await revokeInvite(row.membership.user.public_id);
                  setInviteStateByUserId((current) => ({ ...current, [row.membership.user.public_id]: { kind: 'revoked' } }));
                  if (latestInvite?.userPublicId === row.membership.user.public_id) {
                    setLatestInvite(null);
                  }
                  notifications.show({ color: 'green', title: 'Invite revoked', message: `Revoked ${response.revoked_pending_invite_count ?? 0} pending invite(s).` });
                });
              }}
              onSuspendUser={(row) => {
                void runSensitive(async () => {
                  await suspendBusinessUser(currentBusinessId, row.membership.user.public_id);
                  await refreshMemberships();
                  notifications.show({ color: 'green', title: 'User suspended', message: 'The user was suspended and live sessions were revoked.' });
                });
              }}
              onReactivateUser={(row) => {
                void runSensitive(async () => {
                  await reactivateBusinessUser(currentBusinessId, row.membership.user.public_id);
                  await refreshMemberships();
                  notifications.show({ color: 'green', title: 'User reactivated', message: 'The user can sign in again.' });
                });
              }}
              onArchiveMembership={(row) => {
                void runSensitive(async () => {
                  await archiveBusinessMembership(currentBusinessId, row.membership.public_id);
                  await refreshMemberships();
                  notifications.show({ color: 'green', title: 'Access removed', message: 'The membership was archived.' });
                });
              }}
            />
          </SectionCard>
        </Grid.Col>

        <Grid.Col span={{ base: 12, xl: 4 }}>
          <Stack gap="lg">
            <UserInviteForm
              businessName={businessName}
              disabled={!canManageMemberships}
              submitting={false}
              canAssignBusinessOwner={canAssignBusinessOwner}
              siteOptions={(sitesQuery.data?.sites ?? []).map((site) => ({ value: site.public_id, label: site.name }))}
              onSubmit={handleSubmitUser}
            />

            <SectionCard title="Sensitive actions" description="Membership changes, invite mutations, and suspend/reactivate flows all support fresh re-authentication.">
              <Group gap="sm" align="flex-start" wrap="nowrap">
                <IconShieldLock size={18} />
                <Text c="slate.6" fz="sm">
                  When the backend returns <code>sensitive_reauth_required</code>, RefurbOps asks for your current password and, where policy requires it, a fresh MFA code before retrying the action.
                </Text>
              </Group>
            </SectionCard>
          </Stack>
        </Grid.Col>
      </Grid>

      <ReauthModal
        opened={reauthOpened}
        loading={false}
        error={reauthError}
        onClose={() => {
          setReauthOpened(false);
          setPendingSensitiveAction(null);
          setReauthError(null);
        }}
        onSubmit={finishReauth}
      />
    </Stack>
  );
}
