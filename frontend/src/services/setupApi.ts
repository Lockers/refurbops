import { apiClient } from "./api/client"
import {
  SetupBootstrapRequest,
  SetupBootstrapResponse,
  SetupStatusResponse,
} from "../types/setup"

/**
 * Fetch whether first-time platform bootstrap has already completed.
 */
export async function fetchSetupStatus(): Promise<SetupStatusResponse> {
  const response = await apiClient.get<SetupStatusResponse>("/api/setup/status")
  return response.data
}

/**
 * Bootstrap the first business and admin user.
 */
export async function bootstrapSystem(
  payload: SetupBootstrapRequest
): Promise<SetupBootstrapResponse> {
  const response = await apiClient.post<SetupBootstrapResponse>("/api/setup/bootstrap", payload)
  return response.data
}
