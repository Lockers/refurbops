import { IconInbox } from '@tabler/icons-react';

import { EmptyState } from '@/shared/components/EmptyState';
import { PageHeader } from '@/shared/components/PageHeader';

export function SourceListPage() {
  return (
    <>
      <PageHeader eyebrow="Intake" title="Source records" description="Inbound orders synced from external platforms will appear here." />
      <EmptyState
        title="Source records coming soon"
        description="The inbound source records module is being built. Synced orders from Back Market and other platforms will be listed here once the intake slice is complete."
        icon={<IconInbox size={28} />}
      />
    </>
  );
}