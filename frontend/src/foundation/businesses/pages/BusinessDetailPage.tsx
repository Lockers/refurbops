import { Grid, Stack } from '@mantine/core';
import { useParams } from 'react-router-dom';

import { BusinessActivationPanel } from '@/foundation/businesses/components/BusinessActivationPanel';
import { BusinessForm } from '@/foundation/businesses/components/BusinessForm';
import { BusinessStatusCard } from '@/foundation/businesses/components/BusinessStatusCard';
import { PageHeader } from '@/shared/components/PageHeader';

export function BusinessDetailPage() {
  const { businessId } = useParams();

  return (
    <Stack gap="xl">
      <PageHeader
        eyebrow="Business detail"
        title="Business configuration and readiness"
        description={`Business ID: ${businessId ?? 'unknown'}`}
      />
      <Grid>
        <Grid.Col span={{ base: 12, xl: 7 }}>
          <BusinessForm />
        </Grid.Col>
        <Grid.Col span={{ base: 12, xl: 5 }}>
          <Stack gap="lg">
            <BusinessStatusCard
              id={businessId ?? 'demo'}
              name="Main Refurb Business"
              status="pending_setup"
              subscriptionStatus="pending"
              primarySiteName="Wolverhampton"
            />
            <BusinessActivationPanel />
          </Stack>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
