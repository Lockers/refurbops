import { IconDeviceDesktop } from '@tabler/icons-react';

import { EmptyState } from '@/shared/components/EmptyState';
import { PageHeader } from '@/shared/components/PageHeader';

export function DeviceDetailPage() {
  return (
    <>
      <PageHeader eyebrow="Devices" title="Device detail" description="View and manage individual device records." />
      <EmptyState
        title="Device detail coming soon"
        description="The device detail module is being built. You'll be able to view device history, test results, grading, and inventory status here."
        icon={<IconDeviceDesktop size={28} />}
      />
    </>
  );
}