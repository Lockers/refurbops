import { useEffect, useState } from 'react';
import { Alert, Button, Modal, PasswordInput, Stack, Text, TextInput } from '@mantine/core';

export interface ReauthValues {
  current_password: string;
  code?: string;
}

interface ReauthModalProps {
  opened: boolean;
  loading?: boolean;
  error?: string | null;
  onClose: () => void;
  onSubmit: (values: ReauthValues) => Promise<void> | void;
}

export function ReauthModal({ opened, loading = false, error, onClose, onSubmit }: ReauthModalProps) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [code, setCode] = useState('');

  useEffect(() => {
    if (!opened) {
      setCurrentPassword('');
      setCode('');
    }
  }, [opened]);

  return (
    <Modal opened={opened} onClose={onClose} title="Confirm sensitive action" centered radius="xl">
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          await onSubmit({ current_password: currentPassword, code: code.trim() || undefined });
        }}
      >
        <Stack gap="md">
          <Text c="slate.6" fz="sm">
            This action requires fresh re-authentication. Enter your current password and, if policy asks for it, your current authenticator code.
          </Text>

          {error ? <Alert color="red" variant="light">{error}</Alert> : null}

          <PasswordInput
            label="Current password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.currentTarget.value)}
            required
          />

          <TextInput
            label="Authenticator code"
            placeholder="123456"
            value={code}
            onChange={(event) => setCode(event.currentTarget.value)}
            inputMode="numeric"
            autoComplete="one-time-code"
          />

          <Button type="submit" loading={loading} fullWidth>
            Unlock sensitive actions
          </Button>
        </Stack>
      </form>
    </Modal>
  );
}
