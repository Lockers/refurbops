import { apiRequest } from '@/shared/lib/api-client';
import { env } from '@/shared/lib/env';

export interface BusinessSiteRecord {
  public_id: string;
  business_public_id?: string;
  name: string;
  status: string;
  timezone?: string | null;
  locale?: string | null;
  language?: string | null;
}

export interface BusinessSitesResponse {
  status: 'business_sites_loaded';
  business: {
    public_id: string;
    name: string;
  };
  sites: BusinessSiteRecord[];
}

const sitesUrl = (businessPublicId: string) => `${env.apiBaseUrl}/foundation/businesses/${businessPublicId}/sites`;

export async function listBusinessSites(businessPublicId: string) {
  return apiRequest<BusinessSitesResponse>(sitesUrl(businessPublicId), {
    method: 'GET',
  });
}
