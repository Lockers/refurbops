import { Button, Stack } from '@mantine/core';
import { IconBuildingPlus } from '@tabler/icons-react';

import { BusinessForm } from '@/foundation/businesses/components/BusinessForm';
import { PageHeader } from '@/shared/components/PageHeader';

export function CreateBusinessPage() {
  return (
    <Stack gap="xl">
      <PageHeader
        eyebrow="Create business"
        title="Create a new business tenant"
        description="New businesses should begin in pending setup and move through the setup hub before activation."
        actions={<Button leftSection={<IconBuildingPlus size={16} />}>Save draft</Button>}
      />
      <BusinessForm />
    </Stack>
  );
}
