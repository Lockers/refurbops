"""HTTP helpers used by the learning scraper."""

from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import FetchResponse, ScrapeConfig


class PageFetcher:
    """Fetch pages via the Python standard library.

    The implementation avoids third-party HTTP dependencies so the project can be
    run in a clean Python environment.
    """

    def fetch(self, config: ScrapeConfig) -> FetchResponse:
        """Retrieve a page and normalize common urllib responses."""

        request = Request(config.url, headers={"User-Agent": config.user_agent})
        try:
            with urlopen(request, timeout=config.timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
                status_code = getattr(response, "status", None) or 200
                final_url = response.geturl()
                return FetchResponse(
                    url=final_url,
                    status_code=status_code,
                    text=body,
                    fetch_mode="http",
                    metadata={"fetch_mode": "http", "network_events": []},
                )
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return FetchResponse(
                url=exc.geturl(),
                status_code=exc.code,
                text=body,
                fetch_mode="http",
                metadata={"fetch_mode": "http", "network_events": []},
            )
        except URLError as exc:
            raise ConnectionError(str(exc)) from exc
