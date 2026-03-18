export interface InboundListing {
  sku?: string | null
  product_id?: number | null
  title?: string | null
  grade?: string | null
}

export interface InboundCustomerDocument {
  first_name?: string | null
  last_name?: string | null
  phone?: string | null
  date_of_birth?: string | null
  documents: Array<Record<string, unknown>>
}

export interface InboundReturnAddress {
  address1?: string | null
  address2?: string | null
  city?: string | null
  zipcode?: string | null
  country?: string | null
}

export interface InboundPrice {
  value?: number | null
  currency?: string | null
}

export interface InboundTracking {
  shipper?: string | null
  tracking_number?: string | null
  tracking_url?: string | null
  status_raw?: string | null
  status_group?: string | null
  last_checked_at?: string | null
  last_event_at?: string | null
  likely_arrival_bucket?: string | null
}

export interface InboundLocalState {
  arrived_clicked: boolean
  device_created: boolean
  linked_device_id?: string | null
  hidden_from_inbound: boolean
  archived: boolean
}

export interface InboundQueueRow {
  _id: string
  business_id: string
  source: string
  source_reference: string
  external_status?: string | null
  market?: string | null
  listing_title?: string | null
  listing_grade?: string | null
  customer_full_name?: string | null
  original_price_value?: number | null
  original_price_currency?: string | null
  shipper?: string | null
  tracking_number?: string | null
  tracking_status_group?: string | null
  likely_arrival_bucket?: string | null
  shipping_date?: string | null
  modification_date?: string | null
  arrived_clicked: boolean
  device_created: boolean
  linked_device_id?: string | null
  hidden_from_inbound: boolean
  last_synced_at?: string | null
}

export interface InboundOrderDocument {
  _id?: string | null
  business_id: string
  source: string
  source_reference: string
  external_status?: string | null
  market?: string | null
  creation_date?: string | null
  modification_date?: string | null
  shipping_date?: string | null
  suspension_date?: string | null
  receival_date?: string | null
  payment_date?: string | null
  counter_proposal_date?: string | null
  listing: InboundListing
  customer: InboundCustomerDocument
  return_address: InboundReturnAddress
  original_price: InboundPrice
  counter_offer_price?: InboundPrice | null
  tracking: InboundTracking
  suspend_reasons: Array<Record<string, unknown>>
  counter_offer_reasons: Array<Record<string, unknown>>
  local_state: InboundLocalState
  raw_payload: Record<string, unknown>
  last_seen_in_api?: string | null
  last_synced_at?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface InboundListResponse {
  items: InboundQueueRow[]
  total: number
  page: number
  page_size: number
}

export interface InboundSyncResult {
  business_id: string
  source: string
  fetched: number
  inserted: number
  updated: number
  started_at: string
  completed_at: string
  sync_from?: string | null
}

export interface InboundQueryParams {
  businessId: string
  externalStatus: string
  market: string
  hasTracking?: boolean
  trackingStatusGroup: string
  likelyArrivalBucket: string
  arrivedClicked?: boolean
  page: number
  pageSize: number
}
