import axios from "axios"

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"

/**
 * Shared Axios client used by every frontend service.
 */
export const apiClient = axios.create({
  baseURL: apiBaseUrl,
})

/**
 * Read API health for app-shell visibility.
 */
export async function fetchHealth() {
  const response = await apiClient.get<{
    ok: boolean
    app: string
    environment: string
    database: string
  }>("/health")

  return response.data
}

/**
 * Convert Axios and unknown errors into consistent user-facing messages.
 */
export function getApiErrorMessage(error: unknown, fallbackMessage: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail

    if (typeof detail === "string") {
      return detail
    }

    if (detail && typeof detail === "object" && "message" in detail) {
      return String(detail.message)
    }

    return error.message || fallbackMessage
  }

  if (error instanceof Error) {
    return error.message
  }

  return fallbackMessage
}
