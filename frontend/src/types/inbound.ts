export interface InboundQueueRow {
  _id: string
  business_id: string

  source: string
  source_reference: string

  external_status?: string
  market?: string

  listing_title?: string
  listing_grade?: string

  customer_full_name?: string

  original_price_value?: number
  original_price_currency?: string

  shipper?: string
  tracking_number?: string

  shipping_date?: string
  modification_date?: string

  arrived_clicked: boolean
  device_created: boolean

  last_synced_at?: string
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
}