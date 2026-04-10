import { Alert, Button, Group, Text, ThemeIcon, Title } from '@mantine/core';
import { IconMailCheck } from '@tabler/icons-react';

import { AuthSplitLayout } from '@/auth/components/AuthSplitLayout';

export function VerifyEmailPage() {
  return (
    <AuthSplitLayout
      eyebrow="Auth step"
      title="Email verification is reserved for the backend contract that comes later."
      description="This route stays in the frontend structure now so the auth journey does not churn when the verify-email endpoints arrive."
      badge={
        <Group gap="sm">
          <ThemeIcon radius="xl" color="brand" variant="light" size={38}>
            <IconMailCheck size={18} />
          </ThemeIcon>
          <Text fz="xs" fw={700} tt="uppercase" c="brand.7" style={{ letterSpacing: '0.08em' }}>
            Verify email
          </Text>
        </Group>
      }
      footer={<Button variant="light">Resend verification</Button>}
    >
      <>
        <Title order={2}>Verify your email</Title>
        <Text c="slate.6">
          This route is intentionally styled and routed, but it is not live yet because the backend endpoint does not exist.
        </Text>
        <Alert color="brand" variant="light" radius="xl">
          Keep this route. It is a real future auth step, not filler.
        </Alert>
      </>
    </AuthSplitLayout>
  );
}
