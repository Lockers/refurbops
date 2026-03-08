import axios from "axios"
import {
  SetupBootstrapRequest,
  SetupBootstrapResponse,
  SetupStatusResponse,
} from "../types/setup"

const API = import.meta.env.VITE_API_BASE_URL

export async function fetchSetupStatus(): Promise<SetupStatusResponse> {
  const res = await axios.get(`${API}/api/setup/status`)
  return res.data
}

export async function bootstrapSystem(
  payload: SetupBootstrapRequest
): Promise<SetupBootstrapResponse> {
  const res = await axios.post(`${API}/api/setup/bootstrap`, payload)
  return res.data
}