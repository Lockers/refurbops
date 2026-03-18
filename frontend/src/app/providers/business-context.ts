import { createContext } from "react"

export const DEFAULT_BUSINESS_ID = "biz_001"
export const STORAGE_KEY = "refurbops.business_id"

export interface BusinessContextValue {
  businessId: string
  setBusinessId: (nextBusinessId: string) => void
}

export const BusinessContext = createContext<BusinessContextValue | undefined>(undefined)
