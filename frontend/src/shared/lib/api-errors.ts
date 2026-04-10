import { ApiError } from '@/shared/lib/api-client';

export interface NormalisedApiError {
  message: string;
  reasonCode: string;
  status: number;
  raw: unknown;
}

export function normaliseApiError(error: unknown): NormalisedApiError {
  if (error instanceof ApiError) {
    const body = error.body as { detail?: unknown } | string | null;
    const detail =
      typeof body === 'object' && body !== null && 'detail' in body
        ? (body as { detail?: unknown }).detail
        : body;

    if (typeof detail === 'object' && detail !== null) {
      const message =
        typeof (detail as { message?: unknown }).message === 'string'
          ? ((detail as { message?: string }).message ?? 'Request failed')
          : `Request failed with status ${error.status}`;

      const reasonCode =
        typeof (detail as { reason_code?: unknown }).reason_code === 'string'
          ? ((detail as { reason_code?: string }).reason_code ?? 'structured_error')
          : 'structured_error';

      return { message, reasonCode, status: error.status, raw: error.body };
    }

    if (typeof detail === 'string') {
      return {
        message: detail,
        reasonCode: 'legacy_unstructured_error',
        status: error.status,
        raw: error.body,
      };
    }

    return {
      message: `Request failed with status ${error.status}`,
      reasonCode: 'unknown_api_error',
      status: error.status,
      raw: error.body,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      reasonCode: 'client_error',
      status: 0,
      raw: error,
    };
  }

  return {
    message: 'Unknown error',
    reasonCode: 'unknown_error',
    status: 0,
    raw: error,
  };
}

export function getApiErrorMessage(error: unknown, fallback = 'Request failed'): string {
  const normalised = normaliseApiError(error);
  return normalised.message || fallback;
}

export function getApiErrorReasonCode(error: unknown): string | null {
  const normalised = normaliseApiError(error);
  return normalised.reasonCode || null;
}
