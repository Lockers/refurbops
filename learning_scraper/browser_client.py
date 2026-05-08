"""Optional Playwright-backed browser fetching for JavaScript-heavy sites."""

from __future__ import annotations

import importlib
import time
from dataclasses import dataclass
from typing import Callable, Protocol

from .models import FetchResponse, NetworkEvent, ScrapeConfig


class BrowserSession(Protocol):
    """Protocol for a browser session used by `BrowserFetcher`."""

    def fetch_page(self, config: ScrapeConfig) -> FetchResponse:
        """Load a page in a browser context and return normalized output."""


@dataclass(slots=True)
class BrowserFetcher:
    """Fetch pages in a real browser so JavaScript and XHR/fetch calls execute."""

    session_factory: Callable[[], BrowserSession] | None = None

    def fetch(self, config: ScrapeConfig) -> FetchResponse:
        """Load the page via Playwright or an injected test session."""

        if self.session_factory is not None:
            return self.session_factory().fetch_page(config)

        return _PlaywrightBrowserSession().fetch_page(config)


class _PlaywrightBrowserSession:
    """Default Playwright implementation used at runtime."""

    def fetch_page(self, config: ScrapeConfig) -> FetchResponse:
        """Open a browser, wait for the page to settle, and capture network activity."""

        try:
            sync_api = importlib.import_module("playwright.sync_api")
        except ModuleNotFoundError as exc:
            raise ConnectionError(
                "Playwright is not installed. Run `pip install playwright` and "
                "`playwright install chromium` to use browser mode."
            ) from exc

        network_events: list[NetworkEvent] = []

        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=config.browser_headless)
            context = browser.new_context(user_agent=config.user_agent)
            page = context.new_page()

            def record_response(response: object) -> None:
                """Record successful or error HTTP responses seen by the browser."""

                network_events.append(
                    NetworkEvent(
                        url=response.url,
                        method=response.request.method,
                        resource_type=response.request.resource_type,
                        status_code=response.status,
                    )
                )

            def record_failure(request: object) -> None:
                """Record transport-level request failures such as blocked connections."""

                failure = request.failure
                failure_text = failure["errorText"] if failure else None
                network_events.append(
                    NetworkEvent(
                        url=request.url,
                        method=request.method,
                        resource_type=request.resource_type,
                        failure_text=failure_text,
                    )
                )

            page.on("response", record_response)
            page.on("requestfailed", record_failure)

            response = page.goto(
                config.url,
                wait_until=config.wait_until,
                timeout=int(config.timeout_seconds * 1000),
            )
            if config.wait_for_selector:
                page.wait_for_selector(
                    config.wait_for_selector,
                    timeout=int(config.timeout_seconds * 1000),
                )
            if config.post_load_delay_seconds > 0:
                time.sleep(config.post_load_delay_seconds)

            html = page.content()
            final_url = page.url
            status_code = response.status if response is not None else 200
            browser.close()

        metadata = {
            "fetch_mode": "browser",
            "network_events": [event.__dict__ for event in network_events],
            "wait_until": config.wait_until,
            "wait_for_selector": config.wait_for_selector,
        }
        return FetchResponse(
            url=final_url,
            status_code=status_code,
            text=html,
            fetch_mode="browser",
            network_events=tuple(network_events),
            metadata=metadata,
        )
