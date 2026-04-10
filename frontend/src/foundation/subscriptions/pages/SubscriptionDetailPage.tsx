import { Grid, Stack, Text } from '@mantine/core';
import { useParams } from 'react-router-dom';

import { EntitlementList } from '@/foundation/entitlements/components/EntitlementList';
import { SubscriptionStatusCard } from '@/foundation/subscriptions/components/SubscriptionStatusCard';
import { PageHeader } from '@/shared/components/PageHeader';
import { SectionCard } from '@/shared/components/SectionCard';

export function SubscriptionDetailPage() {
  const { businessId } = useParams();

  return (
    <Stack gap="xl">
      <PageHeader
        eyebrow="Subscriptions"
        title="Subscription and entitlement control"
        description={`Business ID: ${businessId ?? 'unknown'}`}
      />
      <Grid>
        <Grid.Col span={{ base: 12, xl: 7 }}>
          <SectionCard
            title="Commercial state"
            description="Upgrades may activate immediately once paid. Downgrades usually wait for end of term."
          >
            <Text c="slate.7">
              This page should make billing-triggered read-only mode and entitlement loss extremely obvious.
            </Text>
          </SectionCard>
        </Grid.Col>
        <Grid.Col span={{ base: 12, xl: 5 }}>
          <SubscriptionStatusCard />
        </Grid.Col>
      </Grid>
      <EntitlementList />
    </Stack>
  );
}
