import { Table } from '@mantine/core';

const rows = [
  { scope: 'Organisation', target: 'RefurbOps Demo Org', role: 'organisation_admin' },
  { scope: 'Business', target: 'Main Refurb Business', role: 'manager' },
  { scope: 'Site', target: 'Wolverhampton', role: 'viewer' },
];

export function MembershipScopeTable() {
  return (
    <Table withTableBorder verticalSpacing="md" highlightOnHover>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Scope</Table.Th>
          <Table.Th>Target</Table.Th>
          <Table.Th>Role</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {rows.map((row) => (
          <Table.Tr key={`${row.scope}-${row.target}`}>
            <Table.Td>{row.scope}</Table.Td>
            <Table.Td>{row.target}</Table.Td>
            <Table.Td>{row.role}</Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  );
}
