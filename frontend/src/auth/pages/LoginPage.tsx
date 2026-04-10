import {
  Alert,
  Button,
  Code,
  Divider,
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
import { IconAlertCircle, IconTopologyStar3 } from '@tabler/icons-react';
import { useMutation } from '@tanstack/react-query';
import { Navigate, useNavigate } from 'react-router-dom';

import { login } from '@/auth/api';
import { AuthSplitLayout } from '@/auth/components/AuthSplitLayout';
import { useSession } from '@/auth/hooks/useSession';
import { getApiErrorMessage } from '@/shared/lib/api-errors';
import type { LoginRequest } from '@/shared/types/auth';

export function LoginPage() {
  const navigate = useNavigate();
  const { session } = useSession();

  const form = useForm<LoginRequest>({
    initialValues: { email: '', password: '' },
    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Enter a valid email address'),
      password: (value) => (value.length >= 1 ? null : 'Enter your password'),
    },
  });

  const mutation = useMutation({
    mutationFn: async (values: LoginRequest) => ({ response: await login(values), values }),
    onSuccess: async ({ response, values }) => {
      switch (response.next_step) {
        case 'password_change_required':
        case 'password_change_and_mfa_enrollment_required':
          navigate('/change-password', {
            replace: true,
            state: {
              email: values.email,
              currentPassword: values.password,
              user: response.user,
              loginNextStep: response.next_step,
            },
          });
          return;
        case 'mfa_enrollment_required':
          navigate('/mfa/enroll', {
            replace: true,
            state: {
              email: values.email,
              password: values.password,
              user: response.user,
            },
          });
          return;
        case 'session_issue_ready':
          navigate('/mfa', {
            replace: true,
            state: {
              mode: 'session_create',
              email: values.email,
              password: values.password,
              user: response.user,
            },
          });
          return;
        default:
          notifications.show({
            color: 'red',
            title: 'Unsupported auth step',
            message: 'The frontend does not understand the next authentication step.',
          });
      }
    },
    onError: (error) => {
      notifications.show({
        color: 'red',
        title: 'Login failed',
        message: getApiErrorMessage(error, 'The backend rejected the sign-in request.'),
      });
    },
  });

  if (session) {
    return <Navigate to="/app" replace />;
  }

  return (
    <AuthSplitLayout
      eyebrow="Module 00 foundation"
      title="Serious operations UX for refurb, repair, intake, and device control."
      description="Designed for all-day platform use: clear context, deliberate status handling, and admin surfaces ready for future slices."
      badge={
        <Group gap="sm">
          <ThemeIcon radius="xl" color="brand" variant="light" size={38}>
            <IconTopologyStar3 size={18} />
          </ThemeIcon>
          <Text fz="xs" fw={700} tt="uppercase" c="brand.7" style={{ letterSpacing: '0.08em' }}>
            Sign in
          </Text>
        </Group>
      }
    >
      <Stack gap="xl">
        <Stack gap={8}>
          <Title order={2}>Access RefurbOps</Title>
          <Text c="slate.6">
            Login is multi-step: verify credentials, handle password change if required, complete MFA when required, then create a cookie-backed session.
          </Text>
        </Stack>

        <Paper p="xl" radius="2xl" withBorder style={{ background: '#ffffff', borderColor: 'rgba(87, 105, 129, 0.14)' }}>
          <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
            <Stack gap="md">
              <TextInput label="Email" placeholder="you@business.com" autoComplete="email" {...form.getInputProps('email')} />
              <PasswordInput label="Password" placeholder="Enter your password" autoComplete="current-password" {...form.getInputProps('password')} />
              <Button loading={mutation.isPending} type="submit" size="md">
                Continue
              </Button>
            </Stack>
          </form>
        </Paper>

        <Alert color="brand" variant="light" radius="xl" icon={<IconAlertCircle size={16} />}>
          Working today: login, change password, MFA enroll, MFA verify, session create, session refresh, logout, and full session bootstrap from <Code>/auth/session</Code>.
        </Alert>

        <Divider label="Current backend auth scope" labelPosition="center" />
        <Group gap="xs" wrap="wrap">
          <Text size="sm" c="slate.6">Verified credentials</Text>
          <Text size="sm" c="slate.6">•</Text>
          <Text size="sm" c="slate.6">Password change</Text>
          <Text size="sm" c="slate.6">•</Text>
          <Text size="sm" c="slate.6">MFA verify</Text>
          <Text size="sm" c="slate.6">•</Text>
          <Text size="sm" c="slate.6">Cookie session bootstrap</Text>
        </Group>
      </Stack>
    </AuthSplitLayout>
  );
}
