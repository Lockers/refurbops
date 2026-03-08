import axios from "axios"
import { InboundListResponse, InboundSyncResult } from "../types/inbound"

const API = import.meta.env.VITE_API_BASE_URL

export async function syncInbound(businessId: string): Promise<InboundSyncResult> {
  const res = await axios.post(`${API}/api/inbound/backmarket/sync`, {
    business_id: businessId
  })

  return res.data
}

export async function fetchInbound(businessId: string): Promise<InboundListResponse> {
  const res = await axios.get(`${API}/api/inbound`, {
    params: { business_id: businessId }
  })

  return res.data
}