import { Grid, Select, Stack, TextInput } from '@mantine/core';

import { SectionCard } from '@/shared/components/SectionCard';

export function BusinessForm() {
  return (
    <SectionCard
      title="Business profile"
      description="Keep the form narrow, explicit, and easy to scan. Backend remains authoritative for validation and legal transitions."
    >
      <Grid>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <TextInput label="Business name" placeholder="Main Refurb Business" />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <TextInput label="Legal entity" placeholder="RefurbOps Ltd" />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Select label="Default market" placeholder="Select market" data={['GB', 'EU']} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Select label="Operational state" placeholder="Pending setup" data={['pending_setup', 'active', 'read_only', 'suspended']} />
        </Grid.Col>
      </Grid>
      <Stack gap="md" />
    </SectionCard>
  );
}
