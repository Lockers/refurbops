import { apiClient } from "./api/client"
import {
  InboundListResponse,
  InboundOrderDocument,
  InboundQueryParams,
  InboundSyncResult,
} from "../types/inbound"

interface InboundDetailRequest {
  businessId: string
  inboundId: string
}

/**
 * Trigger a manual Back Market sync for the selected business.
 */
export async function syncInbound(businessId: string): Promise<InboundSyncResult> {
  const response = await apiClient.post<InboundSyncResult>("/api/inbound/backmarket/sync", {
    business_id: businessId,
  })

  return response.data
}

/**
 * Fetch the inbound queue using the backend-supported query parameters.
 */
export async function fetchInbound(params: InboundQueryParams): Promise<InboundListResponse> {
  const response = await apiClient.get<InboundListResponse>("/api/inbound", {
    params: {
      business_id: params.businessId,
      external_status: params.externalStatus || undefined,
      market: params.market || undefined,
      has_tracking: params.hasTracking,
      tracking_status_group: params.trackingStatusGroup || undefined,
      likely_arrival_bucket: params.likelyArrivalBucket || undefined,
      arrived_clicked: params.arrivedClicked,
      page: params.page,
      page_size: params.pageSize,
    },
  })

  return response.data
}

/**
 * Fetch a single inbound order document scoped to the selected business.
 */
export async function fetchInboundOrder({ businessId, inboundId }: InboundDetailRequest) {
  const response = await apiClient.get<InboundOrderDocument>(`/api/inbound/${inboundId}`, {
    params: {
      business_id: businessId,
    },
  })

  return response.data
}
