import { Button, Grid, SimpleGrid, Stack } from '@mantine/core';
import { IconBuildingPlus } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { listBusinesses } from '@/foundation/businesses/api';
import { BusinessStatusCard } from '@/foundation/businesses/components/BusinessStatusCard';
import { KpiTile } from '@/shared/components/KpiTile';
import { PageHeader } from '@/shared/components/PageHeader';

export function BusinessListPage() {
  const { data } = useQuery({ queryKey: ['businesses'], queryFn: listBusinesses });

  return (
    <Stack gap="xl">
      <PageHeader
        eyebrow="Businesses"
        title="Business admin and activation control"
        description="Businesses are the primary operational tenant boundary. Their status must stay obvious at list level and detail level."
        actions={
          <Button component={Link} to="/app/businesses/new" leftSection={<IconBuildingPlus size={16} />}>
            Create business
          </Button>
        }
      />

      <Grid>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <KpiTile label="Total businesses" value={String(data?.length ?? 0)} helper="Across the organisation" tone="brand" />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <KpiTile label="Needs setup" value="1" helper="Pending setup or missing activation" tone="warning" />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <KpiTile label="Commercial issues" value="1" helper="Past due or read only" tone="danger" />
        </Grid.Col>
      </Grid>

      <SimpleGrid cols={{ base: 1, xl: 2 }} spacing="lg">
        {(data ?? []).map((business) => (
          <BusinessStatusCard
            key={business.id}
            id={business.id}
            name={business.name}
            status={business.status}
            subscriptionStatus={business.subscription_status}
            primarySiteName={business.primary_site_name}
          />
        ))}
      </SimpleGrid>
    </Stack>
  );
}
