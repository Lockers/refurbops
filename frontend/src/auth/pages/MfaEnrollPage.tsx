import {
  Alert,
  Button,
  Code,
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
import { IconAlertCircle, IconShieldLock } from '@tabler/icons-react';
import { useMutation } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';

import { startMfaEnrollment } from '@/auth/api';
import { AuthSplitLayout } from '@/auth/components/AuthSplitLayout';
import { getApiErrorMessage } from '@/shared/lib/api-errors';
import type { MfaEnrollmentStartRequest } from '@/shared/types/auth';

interface MfaEnrollLocationState {
  email?: string;
  password?: string;
}

export function MfaEnrollPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as MfaEnrollLocationState | null) ?? null;

  const form = useForm<MfaEnrollmentStartRequest>({
    initialValues: {
      email: state?.email || '',
      password: state?.password || '',
    },
    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Enter a valid email address'),
      password: (value) => (value.length >= 1 ? null : 'Enter your password'),
    },
  });

  const mutation = useMutation({
    mutationFn: startMfaEnrollment,
    onSuccess: (response, variables) => {
      navigate('/mfa', {
        replace: true,
        state: {
          mode: 'enrollment_complete',
          email: variables.email,
          password: variables.password,
          secret: response.secret,
          provisioningUri: response.provisioning_uri,
          user: response.user,
        },
      });
    },
    onError: (error) => {
      notifications.show({
        color: 'red',
        title: 'MFA enrollment failed',
        message: getApiErrorMessage(error, 'The backend did not start MFA enrollment.'),
      });
    },
  });

  return (
    <AuthSplitLayout
      eyebrow="Auth step"
      title="Set up multi-factor authentication."
      description="This step requests the live MFA enrollment payload from the backend before verifying the authenticator code and creating a session."
      badge={
        <Group gap="sm">
          <ThemeIcon radius="xl" color="brand" variant="light" size={38}>
            <IconShieldLock size={18} />
          </ThemeIcon>
          <Text fz="xs" fw={700} tt="uppercase" c="brand.7" style={{ letterSpacing: '0.08em' }}>
            MFA enrollment
          </Text>
        </Group>
      }
    >
      <Stack gap="xl">
        <Stack gap={8}>
          <Title order={2}>Start MFA enrollment</Title>
          <Text c="slate.6">The backend returns the secret and provisioning URI, then the frontend moves into verification and session creation.</Text>
        </Stack>

        <Paper p="xl" radius="2xl" withBorder style={{ background: '#ffffff', borderColor: 'rgba(87, 105, 129, 0.14)' }}>
          <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
            <Stack gap="md">
              <TextInput label="Email" autoComplete="email" {...form.getInputProps('email')} />
              <PasswordInput label="Password" autoComplete="current-password" {...form.getInputProps('password')} />
              <Button loading={mutation.isPending} type="submit" size="md">Start MFA enrollment</Button>
            </Stack>
          </form>
        </Paper>

        <Alert color="brand" variant="light" radius="xl" icon={<IconAlertCircle size={16} />}>
          Current expected backend step: <Code>mfa_verify_code</Code>
        </Alert>
      </Stack>
    </AuthSplitLayout>
  );
}
