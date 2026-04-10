import type { SetupHubSummary } from '@/shared/types/foundation';

export async function getSetupHubSummary(): Promise<SetupHubSummary> {
  return {
    organisation: { id: 'org_demo', name: 'RefurbOps Demo Org', business_count: 2 },
    businesses: [
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
    ],
    issues: ['Business Main Refurb Business still needs activation.'],
    next_actions: ['Complete required setup checks.', 'Attach or confirm active subscription.', 'Activate business.'],
  };
}
