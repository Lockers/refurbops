import { Badge } from '@mantine/core';

export function RoleBadge({ role }: { role: string }) {
  return <Badge variant="light">{role}</Badge>;
}
