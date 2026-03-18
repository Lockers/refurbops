import axios from "axios"

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"

export interface HealthResponse {
  ok: boolean
  app: string
  environment: string
  database: string
}

export interface ApiRootResponse {
  name: string
  environment: string
  status: string
}

export interface ApiErrorInfo {
  message: string
  retryAfterSeconds?: number
}

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
  const response = await apiClient.get<HealthResponse>("/health")
  return response.data
}

/**
 * Read backend root metadata so the shell reflects the API contract fully.
 */
export async function fetchApiRoot() {
  const response = await apiClient.get<ApiRootResponse>("/")
  return response.data
}

/**
 * Extract a normalized error payload from Axios and unknown error objects.
 */
export function getApiErrorInfo(error: unknown, fallbackMessage: string): ApiErrorInfo {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail

    if (typeof detail === "string") {
      return { message: detail }
    }

    if (detail && typeof detail === "object") {
      const retryAfterSeconds =
        "retry_after_seconds" in detail && typeof detail.retry_after_seconds === "number"
          ? detail.retry_after_seconds
          : undefined

      if ("message" in detail && typeof detail.message === "string") {
        return {
          message: detail.message,
          retryAfterSeconds,
        }
      }
    }

    return { message: error.message || fallbackMessage }
  }

  if (error instanceof Error) {
    return { message: error.message }
  }

  return { message: fallbackMessage }
}

/**
 * Backwards-compatible helper for pages that only need a message.
 */
export function getApiErrorMessage(error: unknown, fallbackMessage: string) {
  return getApiErrorInfo(error, fallbackMessage).message
}
