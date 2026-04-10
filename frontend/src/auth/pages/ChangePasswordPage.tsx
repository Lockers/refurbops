import {
  Alert,
  Button,
  Group,
  Paper,
  PasswordInput,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconAlertCircle, IconKey } from '@tabler/icons-react';
import { useMutation } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';

import { changePassword } from '@/auth/api';
import { AuthSplitLayout } from '@/auth/components/AuthSplitLayout';
import { getApiErrorMessage } from '@/shared/lib/api-errors';
import type { ChangePasswordRequest } from '@/shared/types/auth';

interface ChangePasswordLocationState {
  email?: string;
  currentPassword?: string;
}

export function ChangePasswordPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as ChangePasswordLocationState | null) ?? null;

  const form = useForm<ChangePasswordRequest>({
    initialValues: {
      email: state?.email || '',
      current_password: state?.currentPassword || '',
      new_password: '',
    },
    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Enter a valid email address'),
      current_password: (value) => (value.length >= 1 ? null : 'Enter your current password'),
      new_password: (value) => (value.length >= 12 ? null : 'Use at least 12 characters'),
    },
  });

  const mutation = useMutation({
    mutationFn: changePassword,
    onSuccess: (response, variables) => {
      if (response.next_step === 'mfa_enrollment_required') {
        navigate('/mfa/enroll', {
          replace: true,
          state: {
            email: variables.email,
            password: variables.new_password,
            user: response.user,
          },
        });
        return;
      }

      navigate('/mfa', {
        replace: true,
        state: {
          mode: 'session_create',
          email: variables.email,
          password: variables.new_password,
          user: response.user,
        },
      });
    },
    onError: (error) => {
      notifications.show({
        color: 'red',
        title: 'Password change failed',
        message: getApiErrorMessage(error, 'Password change failed.'),
      });
    },
  });

  return (
    <AuthSplitLayout
      eyebrow="Auth step"
      title="Update your password before continuing."
      description="The backend requires a new password before this account can finish sign-in."
      badge={
        <Group gap="sm">
          <ThemeIcon radius="xl" color="brand" variant="light" size={38}>
            <IconKey size={18} />
          </ThemeIcon>
          <Text fz="xs" fw={700} tt="uppercase" c="brand.7" style={{ letterSpacing: '0.08em' }}>
            Change password
          </Text>
        </Group>
      }
    >
      <Stack gap="xl">
        <Stack gap={8}>
          <Title order={2}>Set a new password</Title>
          <Text c="slate.6">Once updated, the frontend continues into MFA or session creation based on the backend response.</Text>
        </Stack>

        <Paper p="xl" radius="2xl" withBorder style={{ background: '#ffffff', borderColor: 'rgba(87, 105, 129, 0.14)' }}>
          <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
            <Stack gap="md">
              <TextInput label="Email" autoComplete="email" {...form.getInputProps('email')} />
              <PasswordInput label="Current password" autoComplete="current-password" {...form.getInputProps('current_password')} />
              <PasswordInput label="New password" autoComplete="new-password" {...form.getInputProps('new_password')} />
              <Button loading={mutation.isPending} type="submit">Continue</Button>
            </Stack>
          </form>
        </Paper>

        <Alert color="brand" variant="light" radius="xl" icon={<IconAlertCircle size={16} />}>
          This screen only handles the backend-required password update step. It does not create a session by itself.
        </Alert>
      </Stack>
    </AuthSplitLayout>
  );
}
