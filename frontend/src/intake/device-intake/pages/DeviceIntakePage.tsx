import { IconDeviceMobile } from '@tabler/icons-react';

import { EmptyState } from '@/shared/components/EmptyState';
import { PageHeader } from '@/shared/components/PageHeader';

export function DeviceIntakePage() {
  return (
    <>
      <PageHeader eyebrow="Intake" title="Device intake" description="Manage devices from inbound through testing and grading." />
      <EmptyState
        title="Device intake coming soon"
        description="The device intake module is being built. Once complete, you'll be able to track devices from arrival through testing and into inventory."
        icon={<IconDeviceMobile size={28} />}
      />
    </>
  );
}