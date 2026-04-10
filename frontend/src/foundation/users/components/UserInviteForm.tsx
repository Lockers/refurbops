import { useEffect } from 'react';
import { useForm } from '@mantine/form';
import { Alert, Button, Select, Stack, Text, TextInput } from '@mantine/core';
import { IconMailPlus } from '@tabler/icons-react';

import { SectionCard } from '@/shared/components/SectionCard';

export interface UserInviteFormValues {
  email: string;
  display_name: string;
  role: string;
  scope_type: 'business' | 'site' | 'organisation';
  scope_public_id?: string;
}

interface UserInviteFormProps {
  businessName?: string;
  disabled?: boolean;
  submitting?: boolean;
  canAssignBusinessOwner: boolean;
  siteOptions: Array<{ value: string; label: string }>;
  onSubmit: (values: UserInviteFormValues) => Promise<void> | void;
}

function buildRoleOptions(canAssignBusinessOwner: boolean) {
  const options = [
    { value: 'business_admin', label: 'Business admin' },
    { value: 'manager', label: 'Manager' },
    { value: 'backmarket_admin', label: 'Back Market admin' },
    { value: 'finance', label: 'Finance' },
    { value: 'technician', label: 'Technician' },
    { value: 'viewer', label: 'Viewer' },
  ];

  if (canAssignBusinessOwner) {
    options.unshift({ value: 'business_owner', label: 'Business owner' });
    options.unshift({ value: 'organisation_admin', label: 'Organisation admin' });
    options.push({ value: 'finance_org', label: 'Finance org' });
  }

  return options;
}

export function UserInviteForm({ businessName, disabled = false, submitting = false, canAssignBusinessOwner, siteOptions, onSubmit }: UserInviteFormProps) {
  const form = useForm<UserInviteFormValues>({
    initialValues: {
      email: '',
      display_name: '',
      role: canAssignBusinessOwner ? 'business_admin' : 'manager',
      scope_type: 'business',
      scope_public_id: '',
    },
    validate: {
      email: (value) => (/^\S+@\S+\.\S+$/.test(value) ? null : 'Enter a valid email address'),
      display_name: (value) => (value.trim().length > 0 ? null : 'Display name is required'),
      scope_public_id: (value, values) => {
        if (values.scope_type === 'site' && !value) {
          return 'Select a site for site-scoped access';
        }
        return null;
      },
    },
  });

  const role = form.values.role;

  useEffect(() => {
    if (role === 'business_owner') {
      form.setFieldValue('scope_type', 'business');
      form.setFieldValue('scope_public_id', '');
    }
    if (role === 'organisation_admin' || role === 'finance_org') {
      form.setFieldValue('scope_type', 'organisation');
      form.setFieldValue('scope_public_id', '');
    }
  }, [role]);

  const scopeTypeOptions = [
    { value: 'business', label: 'Business scope' },
    { value: 'site', label: 'Site scope' },
  ];

  if (canAssignBusinessOwner) {
    scopeTypeOptions.unshift({ value: 'organisation', label: 'Organisation scope' });
  }

  const roleScopedLock =
    role === 'business_owner'
      ? 'Business owners must be business-scoped.'
      : role === 'organisation_admin' || role === 'finance_org'
        ? 'This role should stay organisation-scoped.'
        : null;

  return (
    <SectionCard
      title="Add user"
      description={`Create access for ${businessName ?? 'the current business'} and automatically continue into invite creation when the user still needs activation.`}
    >
      <form onSubmit={form.onSubmit(async (values) => onSubmit(values))}>
        <Stack gap="md">
          {roleScopedLock ? <Alert color="blue" variant="light">{roleScopedLock}</Alert> : null}

          <TextInput label="Email" placeholder="new.user@business.com" disabled={disabled || submitting} {...form.getInputProps('email')} />

          <TextInput label="Display name" placeholder="New team member" disabled={disabled || submitting} {...form.getInputProps('display_name')} />

          <Select label="Role" data={buildRoleOptions(canAssignBusinessOwner)} disabled={disabled || submitting} {...form.getInputProps('role')} />

          <Select
            label="Scope"
            data={scopeTypeOptions}
            disabled={disabled || submitting || role === 'business_owner' || role === 'organisation_admin' || role === 'finance_org'}
            {...form.getInputProps('scope_type')}
          />

          {form.values.scope_type === 'site' ? (
            <Select label="Site" placeholder="Choose a site" data={siteOptions} searchable disabled={disabled || submitting} {...form.getInputProps('scope_public_id')} />
          ) : null}

          <Text c="slate.6" fz="sm">
            The backend creates the membership first. If the user is still pending activation, RefurbOps immediately follows with invite creation using the returned user identifier.
          </Text>

          <Button type="submit" leftSection={<IconMailPlus size={16} />} loading={submitting} disabled={disabled}>
            Add user and continue invite flow
          </Button>
        </Stack>
      </form>
    </SectionCard>
  );
}
