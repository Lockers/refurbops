export type BusinessStatus = 'pending_setup' | 'active' | 'read_only' | 'suspended' | 'archived';
export type SiteStatus = 'active' | 'inactive' | 'archived';
export type SubscriptionStatus =
  | 'pending'
  | 'trial'
  | 'active'
  | 'past_due'
  | 'cancel_scheduled'
  | 'expired'
  | 'cancelled';

export interface OrganisationSummary {
  id: string;
  name: string;
  business_count: number;
}

export interface BusinessSummary {
  id: string;
  name: string;
  status: BusinessStatus;
  primary_site_name: string;
  subscription_status: SubscriptionStatus;
}

export interface SiteSummary {
  id: string;
  business_id: string;
  name: string;
  status: SiteStatus;
  timezone: string;
}

export interface UserSummary {
  id: string;
  full_name: string;
  email: string;
  state: string;
}

export interface SubscriptionSummary {
  business_id: string;
  plan_name: string;
  status: SubscriptionStatus;
  add_ons: string[];
}

export interface SetupHubSummary {
  organisation: OrganisationSummary;
  businesses: BusinessSummary[];
  issues: string[];
  next_actions: string[];
}
