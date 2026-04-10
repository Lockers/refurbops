import { List, Text, ThemeIcon } from '@mantine/core';
import { IconCheck } from '@tabler/icons-react';

import { SectionCard } from '@/shared/components/SectionCard';

export function EntitlementList() {
  return (
    <SectionCard title="Entitlements" description="Feature access is the result of backend subscription and membership state.">
      <List
        spacing="md"
        icon={
          <ThemeIcon color="green" radius="xl" variant="light">
            <IconCheck size={14} />
          </ThemeIcon>
        }
      >
        <List.Item>
          <Text>Foundation admin surfaces</Text>
        </List.Item>
        <List.Item>
          <Text>Business and site setup controls</Text>
        </List.Item>
        <List.Item>
          <Text>Back Market connector configuration</Text>
        </List.Item>
      </List>
    </SectionCard>
  );
}
