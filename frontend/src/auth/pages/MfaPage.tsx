import {
  Accordion,
  Alert,
  Button,
  Code,
  CopyButton,
  Divider,
  Group,
  Paper,
  PinInput,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import {
  IconCopy,
  IconCopyCheck,
  IconDeviceMobile,
  IconInfoCircle,
  IconKey,
  IconQrcode,
  IconShieldLock,
} from '@tabler/icons-react';
import { useMutation } from '@tanstack/react-query';
import { QRCodeSVG } from 'qrcode.react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { completeMfaEnrollment, createSession } from '@/auth/api';
import { AuthSplitLayout } from '@/auth/components/AuthSplitLayout';
import { useSession } from '@/auth/hooks/useSession';
import { getApiErrorMessage } from '@/shared/lib/api-errors';
import { queryClient } from '@/shared/lib/query-client';

interface MfaLocationState {
  mode?: 'enrollment_complete' | 'session_create';
  email?: string;
  password?: string;
  secret?: string;
  provisioningUri?: string;
}

interface MfaFormValues {
  code: string;
}

function formatSecret(secret: string) {
  return secret.replace(/\s+/g, '').match(/.{1,4}/g)?.join(' ') ?? secret;
}

function CopyAction({ value, label }: { value: string; label: string }) {
  return (
    <CopyButton value={value} timeout={1600}>
      {({ copied, copy }) => (
        <Button
          variant={copied ? 'filled' : 'light'}
          color={copied ? 'green' : 'brand'}
          leftSection={copied ? <IconCopyCheck size={16} /> : <IconCopy size={16} />}
          onClick={() => {
            copy();
            notifications.show({
              color: copied ? 'green' : 'brand',
              title: copied ? 'Copied again' : 'Copied',
              message: `${label} copied to clipboard.`,
            });
          }}
        >
          {copied ? 'Copied' : `Copy ${label}`}
        </Button>
      )}
    </CopyButton>
  );
}

function StepCard({
  step,
  title,
  description,
}: {
  step: string;
  title: string;
  description: string;
}) {
  return (
    <Paper
      radius="lg"
      p="lg"
      withBorder
      style={{
        borderColor: 'rgba(87, 105, 129, 0.14)',
        background: '#f8fafc',
        height: '100%',
      }}
    >
      <Stack gap="sm">
        <ThemeIcon radius="xl" color="brand" variant="light" size={34}>
          <Text fw={800} size="sm" c="brand.7">
            {step}
          </Text>
        </ThemeIcon>
        <div>
          <Text fw={700} mb={6}>
            {title}
          </Text>
          <Text size="sm" c="slate.6">
            {description}
          </Text>
        </div>
      </Stack>
    </Paper>
  );
}

export function MfaPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { refetchSession } = useSession();
  const state = (location.state as MfaLocationState | null) ?? null;

  const mode = state?.mode ?? 'enrollment_complete';
  const email = state?.email || '';
  const password = state?.password || '';
  const secret = state?.secret || '';
  const provisioningUri = state?.provisioningUri || '';
  const hasEnrollmentDetails = Boolean(secret && provisioningUri);
  const formattedSecret = formatSecret(secret);

  const form = useForm<MfaFormValues>({
    initialValues: { code: '' },
    validate: {
      code: (value) => (value.replace(/\D/g, '').length >= 6 ? null : 'Enter the 6-digit code from your authenticator app'),
    },
  });

  const mutation = useMutation({
    mutationFn: async ({ code }: MfaFormValues) => {
      const normalizedCode = code.replace(/\D/g, '');

      if (mode === 'enrollment_complete') {
        await completeMfaEnrollment({
          email,
          password,
          code: normalizedCode,
        });
      }

      return createSession({
        email,
        password,
        code: normalizedCode,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['session'] });
      await refetchSession();
      notifications.show({
        color: 'green',
        title: 'Session ready',
        message: 'You are now signed in.',
      });
      navigate('/app', { replace: true });
    },
    onError: (error) => {
      notifications.show({
        color: 'red',
        title: mode === 'enrollment_complete' ? 'MFA verification failed' : 'Session creation failed',
        message: getApiErrorMessage(
          error,
          mode === 'enrollment_complete'
            ? 'The verification code was not accepted.'
            : 'The backend could not create the session.'
        ),
      });
    },
  });

  if (!email || !password || (mode === 'enrollment_complete' && !hasEnrollmentDetails)) {
    return (
      <AuthSplitLayout
        eyebrow="Authentication"
        title="MFA state is incomplete"
        description="The frontend does not have the credentials or enrollment payload needed to continue. Restart the auth flow."
      >
        <Stack gap="lg">
          <Alert radius="xl" color="yellow" variant="light" icon={<IconKey size={16} />}>
            This page must be reached from the real backend auth flow. Restart from sign in.
          </Alert>
          <Group>
            <Button component={Link} to="/login" color="brand">
              Back to sign in
            </Button>
          </Group>
        </Stack>
      </AuthSplitLayout>
    );
  }

  return (
    <AuthSplitLayout
      eyebrow="Authentication"
      title={mode === 'enrollment_complete' ? 'Set up and verify your authenticator' : 'Enter your MFA code'}
      description={mode === 'enrollment_complete'
        ? 'Scan the QR code with your authenticator app, then enter the current 6-digit code to complete enrollment and create your session.'
        : 'Enter the current 6-digit code from your authenticator app to create a session.'}
      badge={
        <Group gap="sm">
          <ThemeIcon radius="xl" color="brand" variant="light" size={38}>
            <IconShieldLock size={18} />
          </ThemeIcon>
          <Text fz="xs" fw={700} tt="uppercase" c="brand.7" style={{ letterSpacing: '0.08em' }}>
            {mode === 'enrollment_complete' ? 'MFA setup' : 'MFA verify'}
          </Text>
        </Group>
      }
    >
      <Stack gap="xl">
        {mode === 'enrollment_complete' ? (
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg" verticalSpacing="lg">
            <Paper
              radius="2xl"
              p="xl"
              withBorder
              style={{
                borderColor: 'rgba(29, 99, 237, 0.16)',
                background: 'linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%)',
              }}
            >
              <Stack gap="md" align="center">
                <Group gap="xs" align="center">
                  <ThemeIcon radius="xl" color="brand" variant="light" size={34}>
                    <IconQrcode size={16} />
                  </ThemeIcon>
                  <div>
                    <Text fw={700}>Scan QR code</Text>
                    <Text size="sm" c="slate.6">Fastest setup path</Text>
                  </div>
                </Group>

                <Paper
                  radius="lg"
                  p="md"
                  withBorder
                  style={{
                    background: '#ffffff',
                    borderColor: 'var(--app-panel-border, rgba(87, 105, 129, 0.14))',
                    boxShadow: '0 12px 32px rgba(15, 23, 42, 0.06)',
                  }}
                >
                  <QRCodeSVG value={provisioningUri} size={240} includeMargin level="M" />
                </Paper>

                <Text size="sm" c="slate.6" ta="center" maw={320}>
                  Open your authenticator app, choose add account, then scan this code.
                </Text>
              </Stack>
            </Paper>

            <Stack gap="lg">
              <Paper
                radius="2xl"
                p="xl"
                withBorder
                style={{
                  borderColor: 'var(--app-panel-border, rgba(87, 105, 129, 0.14))',
                  background: '#ffffff',
                }}
              >
                <Stack gap="md">
                  <Group gap="xs" align="center">
                    <ThemeIcon radius="xl" color="brand" variant="light" size={34}>
                      <IconKey size={16} />
                    </ThemeIcon>
                    <div>
                      <Text fw={700}>Manual setup key</Text>
                      <Text size="sm" c="slate.6">Use this only if QR scanning is not possible</Text>
                    </div>
                  </Group>

                  <Code
                    block
                    style={{
                      fontSize: 22,
                      lineHeight: 1.35,
                      textAlign: 'center',
                      padding: '18px 20px',
                      borderRadius: 16,
                      wordBreak: 'break-word',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {formattedSecret}
                  </Code>

                  <Group justify="space-between" gap="md" wrap="wrap">
                    <Stack gap={2}>
                      <Text size="sm" fw={600}>Account name</Text>
                      <Text size="sm" c="slate.6">{email}</Text>
                    </Stack>
                    <Stack gap={2}>
                      <Text size="sm" fw={600}>Code type</Text>
                      <Text size="sm" c="slate.6">Time based</Text>
                    </Stack>
                  </Group>

                  <CopyAction value={secret} label="secret" />
                </Stack>
              </Paper>

              <Alert radius="lg" color="brand" variant="light" icon={<IconDeviceMobile size={16} />}>
                After adding the account in your authenticator app, enter the current 6-digit code below. The frontend will complete enrollment and immediately create the session.
              </Alert>
            </Stack>
          </SimpleGrid>
        ) : null}

        <Paper radius="2xl" p="xl" withBorder style={{ borderColor: 'var(--app-panel-border, rgba(87, 105, 129, 0.14))', background: '#ffffff' }}>
          <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
            <Stack gap="md">
              <div>
                <Text fw={700}>Authenticator code</Text>
                <Text size="sm" c="slate.6">Enter the current 6-digit code for {email}.</Text>
              </div>

              <PinInput
                length={6}
                oneTimeCode
                type="number"
                size="lg"
                value={form.values.code}
                onChange={(value) => form.setFieldValue('code', value)}
                error={!!form.errors.code}
              />

              <Group justify="space-between" align="center" wrap="wrap">
                <Button component={Link} to="/login" variant="subtle">Back to sign in</Button>
                <Button loading={mutation.isPending} type="submit" size="md">
                  {mode === 'enrollment_complete' ? 'Verify and sign in' : 'Sign in'}
                </Button>
              </Group>
            </Stack>
          </form>
        </Paper>

        {mode === 'enrollment_complete' ? (
          <div>
            <Divider label="How to complete setup" labelPosition="left" mb="lg" />
            <SimpleGrid cols={{ base: 1, md: 3 }} spacing="md">
              <StepCard step="1" title="Open your authenticator app" description="Use Google Authenticator, Microsoft Authenticator, or any other app that supports time-based codes." />
              <StepCard step="2" title="Add a new account" description="Choose add account, then scan the QR code. If you cannot scan it, use the manual setup key instead." />
              <StepCard step="3" title="Enter the current code" description="The frontend will verify the code against the backend, complete MFA enrollment, and create your authenticated session." />
            </SimpleGrid>
          </div>
        ) : null}

        <Accordion variant="separated" radius="lg">
          <Accordion.Item value="advanced">
            <Accordion.Control icon={<IconInfoCircle size={16} />}>Advanced details</Accordion.Control>
            <Accordion.Panel>
              <Text size="sm" c="slate.6">
                The backend stores session state server-side and issues secure cookies. This page only handles the MFA verification step required before entering the protected app shell.
              </Text>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      </Stack>
    </AuthSplitLayout>
  );
}
