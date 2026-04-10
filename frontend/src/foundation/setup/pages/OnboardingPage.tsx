import { Button, Grid, List, Paper, Stack, Text, ThemeIcon } from '@mantine/core';
import { IconBuildingWarehouse, IconCheck, IconUsers } from '@tabler/icons-react';

import { PageHeader } from '@/shared/components/PageHeader';
import { SectionCard } from '@/shared/components/SectionCard';

export function OnboardingPage() {
  return (
    <Stack gap="xl">
      <PageHeader
        eyebrow="Onboarding"
        title="Initial platform setup"
        description="The first organisation admin flow should feel guided, explicit, and safe."
        actions={<Button>Create organisation foundation</Button>}
      />

      <Grid>
        <Grid.Col span={{ base: 12, xl: 8 }}>
          <SectionCard
            title="What onboarding should create"
            description="Initial organisation, first business, first site, and first admin membership."
          >
            <List
              spacing="md"
              icon={
                <ThemeIcon color="brand" radius="xl" variant="light">
                  <IconCheck size={14} />
                </ThemeIcon>
              }
            >
              <List.Item>Organisation umbrella created</List.Item>
              <List.Item>First business created in pending setup</List.Item>
              <List.Item>First site attached to the business</List.Item>
              <List.Item>Organisation admin membership established</List.Item>
            </List>
          </SectionCard>
        </Grid.Col>
        <Grid.Col span={{ base: 12, xl: 4 }}>
          <Stack gap="lg">
            <Paper p="lg" radius="xl" withBorder>
              <Stack gap="xs">
                <ThemeIcon color="brand" variant="light" radius="xl" size={40}>
                  <IconBuildingWarehouse size={18} />
                </ThemeIcon>
                <Text fw={700}>Business starts in pending setup</Text>
                <Text c="slate.6" fz="sm">
                  The setup hub should make activation requirements obvious.
                </Text>
              </Stack>
            </Paper>
            <Paper p="lg" radius="xl" withBorder>
              <Stack gap="xs">
                <ThemeIcon color="brand" variant="light" radius="xl" size={40}>
                  <IconUsers size={18} />
                </ThemeIcon>
                <Text fw={700}>Permissions stay backend authoritative</Text>
                <Text c="slate.6" fz="sm">
                  Frontend should reflect scope and blocked states clearly but never enforce legality alone.
                </Text>
              </Stack>
            </Paper>
          </Stack>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
