import { Grid, Stack, Text } from '@mantine/core';
import { useParams } from 'react-router-dom';

import { MembershipScopeTable } from '@/foundation/memberships/components/MembershipScopeTable';
import { PageHeader } from '@/shared/components/PageHeader';
import { SectionCard } from '@/shared/components/SectionCard';

export function UserDetailPage() {
  const { userId } = useParams();

  return (
    <Stack gap="xl">
      <PageHeader
        eyebrow="User detail"
        title="User profile and memberships"
        description={`User ID: ${userId ?? 'unknown'}`}
      />
      <Grid>
        <Grid.Col span={{ base: 12, xl: 5 }}>
          <SectionCard title="Profile summary" description="Core account information and state.">
            <Stack gap="xs">
              <Text fw={700}>Matt Lock</Text>
              <Text c="slate.6">matt@example.com</Text>
              <Text c="slate.6">State: active</Text>
            </Stack>
          </SectionCard>
        </Grid.Col>
        <Grid.Col span={{ base: 12, xl: 7 }}>
          <MembershipScopeTable />
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
