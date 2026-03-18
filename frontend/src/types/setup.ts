export interface SetupStatusResponse {
  is_configured: boolean
}

export interface BackMarketSetupConfig {
  enabled: boolean
  api_key: string
  accept_language: string
  company_name: string
  integration_name: string
  contact_email: string
  proxy_url: string
}

export interface SetupBusinessPayload {
  _id: string
  name: string
  vat_registered: boolean
  vat_scheme: string
  vat_period: string
  vat_period_start: string
  backmarket: BackMarketSetupConfig
}

export interface SetupUserPayload {
  _id: string
  name: string
  email: string
  role: string
}

export interface SetupBootstrapRequest {
  business: SetupBusinessPayload
  user: SetupUserPayload
}

export interface SetupBootstrapResponse {
  business_id: string
  user_id: string
  created: boolean
}
