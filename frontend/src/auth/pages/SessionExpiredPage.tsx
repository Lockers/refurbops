import { Button, Group, Text, ThemeIcon, Title } from '@mantine/core';
import { IconClockPause } from '@tabler/icons-react';
import { Link } from 'react-router-dom';

import { AuthSplitLayout } from '@/auth/components/AuthSplitLayout';

export function SessionExpiredPage() {
  return (
    <AuthSplitLayout
      eyebrow="Session state"
      title="Your server-side session is no longer valid."
      description="This is the correct frontend response for expired or revoked session state. Sign in again to continue once the session API is available."
      badge={
        <Group gap="sm">
          <ThemeIcon radius="xl" color="yellow" variant="light" size={38}>
            <IconClockPause size={18} />
          </ThemeIcon>
          <Text fz="xs" fw={700} tt="uppercase" c="yellow.7" style={{ letterSpacing: '0.08em' }}>
            Session expired
          </Text>
        </Group>
      }
      footer={<Button component={Link} to="/login">Back to sign in</Button>}
    >
      <>
        <Title order={2}>Session expired</Title>
        <Text c="slate.6">
          Your server-side session is no longer valid. Sign in again to continue.
        </Text>
      </>
    </AuthSplitLayout>
  );
}
