import { Alert, Button, Group, Stack, Text, ThemeIcon, Title } from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import { Link } from 'react-router-dom';

import { AuthSplitLayout } from '@/auth/components/AuthSplitLayout';

export function AuthVerifiedPage() {
  return (
    <AuthSplitLayout
      eyebrow="Auth flow"
      title="This route is now a safe fallback only."
      description="The frontend should normally move through password, MFA, and session creation directly without pausing here."
      badge={
        <Group gap="sm">
          <ThemeIcon radius="xl" color="yellow" variant="light" size={38}>
            <IconAlertCircle size={18} />
          </ThemeIcon>
          <Text fz="xs" fw={700} tt="uppercase" c="yellow.7" style={{ letterSpacing: '0.08em' }}>
            Fallback route
          </Text>
        </Group>
      }
      footer={<Button component={Link} to="/login">Back to sign in</Button>}
    >
      <Stack gap="lg">
        <Title order={2}>Continue from sign in</Title>
        <Alert color="yellow" variant="light" radius="xl" icon={<IconAlertCircle size={16} />}>
          Use the normal login flow. This page remains only as a fallback while auth routing continues to harden.
        </Alert>
      </Stack>
    </AuthSplitLayout>
  );
}
