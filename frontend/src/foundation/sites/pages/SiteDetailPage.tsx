import { Grid, Stack } from '@mantine/core';
import { useParams } from 'react-router-dom';

import { SiteForm } from '@/foundation/sites/components/SiteForm';
import { SiteStatusCard } from '@/foundation/sites/components/SiteStatusCard';
import { PageHeader } from '@/shared/components/PageHeader';

export function SiteDetailPage() {
  const { siteId } = useParams();

  return (
    <Stack gap="xl">
      <PageHeader eyebrow="Site detail" title="Site configuration" description={`Site ID: ${siteId ?? 'unknown'}`} />
      <Grid>
        <Grid.Col span={{ base: 12, xl: 7 }}>
          <SiteForm />
        </Grid.Col>
        <Grid.Col span={{ base: 12, xl: 5 }}>
          <SiteStatusCard />
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
