from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings


BUYBACK_ORDERS_PATH = "/ws/buyback/v1/orders"


class BackMarketClientError(Exception):
    """Base exception for Back Market client errors."""


class BackMarketConfigurationError(BackMarketClientError):
    """Raised when required Back Market client configuration is missing."""


class BackMarketAuthenticationError(BackMarketClientError):
    """Raised for authentication or authorization failures."""


class BackMarketRateLimitError(BackMarketClientError):
    """
    Raised when the Back Market API or Cloudflare rate-limits the request.

    Attributes
    ----------
    retry_after_seconds:
        Parsed retry delay if available.
    """

    def __init__(self, message: str, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class BackMarketTransientError(BackMarketClientError):
    """Raised for retryable transport or upstream availability issues."""


class BackMarketResponseError(BackMarketClientError):
    """Raised when the Back Market API returns an unexpected response."""


@dataclass(slots=True)
class BackMarketRequestContext:
    """
    Request context for a single Back Market call.

    Keeping this small and explicit makes it easier to reuse the client across
    business-scoped calls without leaking config into global state.
    """

    api_key: str
    accept_language: str
    user_agent: str
    proxy_url: str | None = None


class BackMarketClient:
    """
    Async HTTP client for Back Market API calls.

    Module 01 scope:
    - Business-scoped headers
    - Oxylabs proxy support
    - Paginated buyback order fetch
    - Retry/backoff for transient failures
    - Clear exception mapping for 403/429/5xx/Cloudflare cases

    This client is intentionally lean for the first inbound slice, but its
    structure is ready for later hardening and endpoint expansion.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int = 3,
        retry_base_delay_seconds: float = 1.0,
        max_retry_delay_seconds: float = 10.0,
    ) -> None:
        settings = get_settings()

        self._base_url = (base_url or settings.backmarket_base_url).rstrip("/")
        self._timeout_seconds = timeout_seconds or settings.backmarket_timeout_seconds
        self._max_retries = max_retries
        self._retry_base_delay_seconds = retry_base_delay_seconds
        self._max_retry_delay_seconds = max_retry_delay_seconds

    async def fetch_buyback_orders(
        self,
        *,
        api_key: str,
        accept_language: str,
        user_agent: str,
        proxy_url: str | None,
        modification_date_from: str | None,
        page: int = 1,
    ) -> dict[str, Any]:
        """
        Fetch one page of Back Market buyback orders.

        Parameters
        ----------
        api_key:
            Business-scoped Back Market API key.
        accept_language:
            Business-scoped Back Market language/market header, e.g. `en-gb`.
        user_agent:
            Generated business-scoped User-Agent string.
        proxy_url:
            Optional Oxylabs rotating proxy URL.
        modification_date_from:
            Optional lower-bound filter for `modificationDate`.
        page:
            1-based Back Market page number.

        Returns
        -------
        dict[str, Any]
            Parsed JSON payload from Back Market.

        Raises
        ------
        BackMarketClientError
            For all known Back Market transport/response failures.
        """
        context = BackMarketRequestContext(
            api_key=api_key,
            accept_language=accept_language,
            user_agent=user_agent,
            proxy_url=proxy_url,
        )

        params: dict[str, Any] = {"page": page}
        if modification_date_from:
            params["modificationDate"] = modification_date_from

        return await self._request_json(
            method="GET",
            path=BUYBACK_ORDERS_PATH,
            context=context,
            params=params,
        )

    async def _request_json(
        self,
        *,
        method: str,
        path: str,
        context: BackMarketRequestContext,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a JSON API request with retry/backoff handling.

        Retryable cases:
        - network/timeout errors
        - 429 rate limiting
        - 5xx upstream failures
        - Cloudflare/temporary availability issues

        Non-retryable cases:
        - missing config
        - 401/403 auth failures
        - invalid response payloads
        - 4xx business/validation errors except 429
        """
        self._validate_context(context)

        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 2):
            try:
                async with self._build_http_client(context) as client:
                    response = await client.request(
                        method=method,
                        url=path,
                        params=params,
                        json=json_body,
                    )

                return self._handle_response(response)

            except BackMarketRateLimitError as exc:
                last_error = exc
                if attempt > self._max_retries:
                    raise

                delay = self._get_retry_delay(
                    attempt=attempt,
                    retry_after_seconds=exc.retry_after_seconds,
                )
                await asyncio.sleep(delay)

            except BackMarketTransientError as exc:
                last_error = exc
                if attempt > self._max_retries:
                    raise

                delay = self._get_retry_delay(attempt=attempt)
                await asyncio.sleep(delay)

            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt > self._max_retries:
                    raise BackMarketTransientError("Back Market request timed out.") from exc

                delay = self._get_retry_delay(attempt=attempt)
                await asyncio.sleep(delay)

            except httpx.TransportError as exc:
                last_error = exc
                if attempt > self._max_retries:
                    raise BackMarketTransientError("Back Market transport error.") from exc

                delay = self._get_retry_delay(attempt=attempt)
                await asyncio.sleep(delay)

        raise BackMarketTransientError("Back Market request failed after retries.") from last_error

    def _build_http_client(self, context: BackMarketRequestContext) -> httpx.AsyncClient:
        """
        Build an async HTTP client for a single Back Market request sequence.
        """
        headers = self._build_headers(context)

        client_kwargs: dict[str, Any] = {
            "base_url": self._base_url,
            "headers": headers,
            "timeout": self._timeout_seconds,
            "follow_redirects": True,
        }

        if context.proxy_url:
            client_kwargs["proxy"] = context.proxy_url

        return httpx.AsyncClient(**client_kwargs)

    @staticmethod
    def _build_headers(context: BackMarketRequestContext) -> dict[str, str]:
        """
        Build required headers for Back Market API requests.
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Language": context.accept_language,
            "Authorization": f"Basic {context.api_key}",
            "User-Agent": context.user_agent,
        }

    @staticmethod
    def _validate_context(context: BackMarketRequestContext) -> None:
        """
        Validate required request context before any HTTP call is attempted.
        """
        if not context.api_key:
            raise BackMarketConfigurationError("Back Market API key is missing.")
        if not context.accept_language:
            raise BackMarketConfigurationError("Back Market Accept-Language is missing.")
        if not context.user_agent:
            raise BackMarketConfigurationError("Back Market User-Agent is missing.")

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        Map HTTP responses into either JSON payloads or typed client errors.
        """
        status_code = response.status_code

        if 200 <= status_code < 300:
            return self._parse_json_response(response)

        if status_code == 401:
            raise BackMarketAuthenticationError("Back Market authentication failed (401).")

        if status_code == 403:
            raise self._handle_forbidden(response)

        if status_code == 429:
            retry_after_seconds = self._parse_retry_after_seconds(response)
            raise BackMarketRateLimitError(
                "Back Market rate limit exceeded (429).",
                retry_after_seconds=retry_after_seconds,
            )

        if status_code in {500, 502, 503, 504}:
            retry_after_seconds = self._parse_retry_after_seconds(response)
            message = self._extract_error_message(response) or f"Back Market upstream error ({status_code})."

            if status_code == 503:
                # Cloudflare/service-availability cases should be treated as transient.
                raise BackMarketTransientError(
                    f"{message} Retry after: {retry_after_seconds}s"
                    if retry_after_seconds is not None
                    else message
                )

            raise BackMarketTransientError(message)

        message = self._extract_error_message(response) or f"Unexpected Back Market response ({status_code})."
        raise BackMarketResponseError(message)

    def _handle_forbidden(self, response: httpx.Response) -> BackMarketClientError:
        """
        Handle 403 responses, including Cloudflare and bot-challenge cases.
        """
        cf_ray = response.headers.get("cf-ray")
        parsed_body = self._safe_parse_json(response)

        # Bot management example:
        # {"errors":[{"code":"bot-need-challenge","message":"Forbidden","challengePath":"/..."}]}
        error_code = self._extract_error_code(parsed_body)
        if error_code == "bot-need-challenge":
            message = "Back Market bot challenge required (403)."
            if cf_ray:
                message = f"{message} cf-ray={cf_ray}"
            return BackMarketAuthenticationError(message)

        message = self._extract_error_message(response) or "Back Market request forbidden (403)."
        if cf_ray:
            message = f"{message} cf-ray={cf_ray}"

        return BackMarketAuthenticationError(message)

    @staticmethod
    def _parse_json_response(response: httpx.Response) -> dict[str, Any]:
        """
        Parse a successful JSON response body.
        """
        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise BackMarketResponseError("Back Market returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise BackMarketResponseError("Back Market returned a non-object JSON payload.")

        return data

    @staticmethod
    def _safe_parse_json(response: httpx.Response) -> dict[str, Any] | None:
        """
        Parse JSON if possible, otherwise return None.
        """
        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError):
            return None

        return data if isinstance(data, dict) else None

    @staticmethod
    def _extract_error_code(payload: dict[str, Any] | None) -> str | None:
        """
        Extract a likely error code from a Back Market error payload.
        """
        if not payload:
            return None

        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                code = first.get("code")
                if isinstance(code, str):
                    return code

        error = payload.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            if isinstance(code, str):
                return code

        return None

    def _extract_error_message(self, response: httpx.Response) -> str | None:
        """
        Extract the most useful error message from JSON or plain-text responses.
        """
        payload = self._safe_parse_json(response)
        if payload:
            # Back Market problem+json pattern:
            # {"error":{"message":"...","code":"..."}}
            error = payload.get("error")
            if isinstance(error, dict):
                message = error.get("message")
                if isinstance(message, str) and message.strip():
                    return message.strip()

            # Bot-management/simple errors list pattern:
            # {"errors":[{"message":"Forbidden"}]}
            errors = payload.get("errors")
            if isinstance(errors, list) and errors:
                first = errors[0]
                if isinstance(first, dict):
                    message = first.get("message")
                    if isinstance(message, str) and message.strip():
                        return message.strip()

        text = response.text.strip()
        if text:
            return text[:500]

        return None

    @staticmethod
    def _parse_retry_after_seconds(response: httpx.Response) -> float | None:
        """
        Parse Retry-After header when present.

        Only the simple numeric seconds form is supported for now.
        """
        retry_after = response.headers.get("Retry-After")
        if not retry_after:
            return None

        try:
            value = float(retry_after)
        except ValueError:
            return None

        return value if value >= 0 else None

    def _get_retry_delay(
        self,
        *,
        attempt: int,
        retry_after_seconds: float | None = None,
    ) -> float:
        """
        Compute a bounded retry delay.

        Rules:
        - Prefer Retry-After when present
        - Otherwise use simple exponential backoff
        """
        if retry_after_seconds is not None:
            return min(retry_after_seconds, self._max_retry_delay_seconds)

        delay = self._retry_base_delay_seconds * (2 ** (attempt - 1))
        return min(delay, self._max_retry_delay_seconds)
