import { Badge } from '@mantine/core';
import {
  IconAlertTriangle,
  IconBan,
  IconCircleCheck,
  IconClockHour4,
  IconEye,
  IconHistory,
  IconReceipt,
  IconUserPlus,
} from '@tabler/icons-react';
import type { ReactNode } from 'react';

const statusMap: Record<string, { color: string; label: string; icon: ReactNode }> = {
  pending_setup: { color: 'blue', label: 'Pending setup', icon: <IconClockHour4 size={12} /> },
  pending: { color: 'blue', label: 'Pending', icon: <IconClockHour4 size={12} /> },
  pending_activation: { color: 'blue', label: 'Pending activation', icon: <IconUserPlus size={12} /> },
  trial: { color: 'brand', label: 'Trial', icon: <IconReceipt size={12} /> },
  active: { color: 'green', label: 'Active', icon: <IconCircleCheck size={12} /> },
  read_only: { color: 'yellow', label: 'Read only', icon: <IconEye size={12} /> },
  suspended: { color: 'red', label: 'Suspended', icon: <IconBan size={12} /> },
  archived: { color: 'gray', label: 'Archived', icon: <IconHistory size={12} /> },
  inactive: { color: 'gray', label: 'Inactive', icon: <IconHistory size={12} /> },
  expired: { color: 'red', label: 'Expired', icon: <IconAlertTriangle size={12} /> },
  cancelled: { color: 'gray', label: 'Cancelled', icon: <IconHistory size={12} /> },
  cancel_scheduled: { color: 'violet', label: 'Cancel scheduled', icon: <IconAlertTriangle size={12} /> },
  past_due: { color: 'yellow', label: 'Past due', icon: <IconAlertTriangle size={12} /> },
  pending_invite: { color: 'blue', label: 'Pending invite', icon: <IconClockHour4 size={12} /> },
};

export function StatusBadge({ value }: { value: string }) {
  const config = statusMap[value] ?? {
    color: 'gray',
    label: value.replaceAll('_', ' '),
    icon: <IconHistory size={12} />,
  };

  return (
    <Badge color={config.color} leftSection={config.icon} size="md" variant="light">
      {config.label}
    </Badge>
  );
}
