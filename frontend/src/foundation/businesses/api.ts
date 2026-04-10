import type { BusinessSummary } from '@/shared/types/foundation';

export async function listBusinesses(): Promise<BusinessSummary[]> {
  return [
    {
      id: 'bus_demo_1',
      name: 'Main Refurb Business',
      status: 'pending_setup',
      primary_site_name: 'Wolverhampton',
      subscription_status: 'pending',
    },
    {
      id: 'bus_demo_2',
      name: 'Trade-In Unit',
      status: 'read_only',
      primary_site_name: 'Birmingham',
      subscription_status: 'past_due',
    },
  ];
}
