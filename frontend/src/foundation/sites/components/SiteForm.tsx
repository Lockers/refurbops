import { Grid, Select, TextInput } from '@mantine/core';

import { SectionCard } from '@/shared/components/SectionCard';

export function SiteForm() {
  return (
    <SectionCard title="Site profile" description="Physical site configuration and basic operational metadata.">
      <Grid>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <TextInput label="Site name" placeholder="Wolverhampton" />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Select label="Timezone" placeholder="Europe/London" data={['Europe/London', 'UTC']} />
        </Grid.Col>
      </Grid>
    </SectionCard>
  );
}
