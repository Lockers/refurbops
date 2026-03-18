"""Tests for the standalone learning scraper."""

from __future__ import annotations

from dataclasses import dataclass

from learning_scraper.models import FetchResponse, RetryPolicy, ScrapeConfig
from learning_scraper.runner import LearningScraper


@dataclass(slots=True)
class FakeFetcher:
    """Simple fetcher stub that returns canned responses in order."""

    responses: list[FetchResponse]

    def fetch(self, config: ScrapeConfig) -> FetchResponse:
        """Pop the next canned response for the current test."""

        return self.responses.pop(0)


@dataclass(slots=True)
class ErrorFetcher:
    """Fetcher stub that always raises a connection error."""

    message: str

    def fetch(self, config: ScrapeConfig) -> FetchResponse:
        """Raise a deterministic transport error."""

        raise ConnectionError(self.message)


def test_scraper_retries_short_page_then_succeeds() -> None:
    """The scraper should retry when the first page is too short."""

    scraper = LearningScraper(
        fetcher=FakeFetcher(
            responses=[
                FetchResponse(
                    url="https://example.com/page",
                    status_code=200,
                    text="<html><title>Short</title><body>tiny</body></html>",
                ),
                FetchResponse(
                    url="https://example.com/page",
                    status_code=200,
                    text=(
                        "<html><title>Ready</title><body>"
                        "This example page contains enough readable text to satisfy the "
                        "learning scraper judgement engine and includes the word example."
                        "</body></html>"
                    ),
                ),
            ]
        )
    )
    result = scraper.run(
        ScrapeConfig(
            url="https://example.com/page",
            min_text_length=50,
            required_keywords=("example",),
            retry_policy=RetryPolicy(max_attempts=2),
        )
    )

    assert result.success is True
    assert len(result.attempts) == 2
    assert result.attempts[0].decision == "retry"
    assert result.attempts[1].decision == "accept"
    assert result.extraction is not None
    assert result.extraction.title == "Ready"


def test_scraper_retries_retryable_status_and_fails() -> None:
    """The scraper should stop after exhausting retryable HTTP failures."""

    scraper = LearningScraper(
        fetcher=FakeFetcher(
            responses=[
                FetchResponse(url="https://example.com/page", status_code=503, text="Service unavailable"),
                FetchResponse(url="https://example.com/page", status_code=503, text="Service unavailable"),
            ]
        )
    )
    result = scraper.run(
        ScrapeConfig(
            url="https://example.com/page",
            retry_policy=RetryPolicy(max_attempts=2),
        )
    )

    assert result.success is False
    assert len(result.attempts) == 2
    assert result.failure_reason == "Retryable status code: 503"


def test_scraper_retries_for_forbidden_keyword_and_fails() -> None:
    """The scraper should retry when content looks like a bot challenge."""

    scraper = LearningScraper(
        fetcher=FakeFetcher(
            responses=[
                FetchResponse(
                    url="https://example.com/page",
                    status_code=200,
                    text=(
                        "<html><title>Blocked</title><body>"
                        "Please complete the CAPTCHA challenge before continuing."
                        "</body></html>"
                    ),
                ),
                FetchResponse(
                    url="https://example.com/page",
                    status_code=200,
                    text=(
                        "<html><title>Blocked</title><body>"
                        "Please complete the CAPTCHA challenge before continuing."
                        "</body></html>"
                    ),
                ),
            ]
        )
    )
    result = scraper.run(
        ScrapeConfig(
            url="https://example.com/page",
            min_text_length=10,
            retry_policy=RetryPolicy(max_attempts=2),
        )
    )

    assert result.success is False
    assert len(result.attempts) == 2
    assert "forbidden keyword" in result.failure_reason.lower()


def test_scraper_returns_transport_failure_after_retries() -> None:
    """Transport failures should be retried and then surfaced clearly."""

    scraper = LearningScraper(fetcher=ErrorFetcher(message="timed out"))
    result = scraper.run(
        ScrapeConfig(
            url="https://example.com/page",
            retry_policy=RetryPolicy(max_attempts=2),
        )
    )

    assert result.success is False
    assert len(result.attempts) == 2
    assert result.failure_reason == "HTTP error: timed out"


def test_scraper_retries_when_required_network_call_is_missing() -> None:
    """Browser-mode judgement should retry if the expected API call never appears."""

    scraper = LearningScraper(
        fetcher=FakeFetcher(
            responses=[
                FetchResponse(
                    url="https://example.com/app",
                    status_code=200,
                    text="<html><title>App</title><body>Loaded app shell with enough text.</body></html>",
                    fetch_mode="browser",
                    metadata={
                        "fetch_mode": "browser",
                        "network_events": [
                            {
                                "url": "https://example.com/static/app.js",
                                "method": "GET",
                                "resource_type": "script",
                                "status_code": 200,
                                "failure_text": None,
                            }
                        ],
                    },
                ),
                FetchResponse(
                    url="https://example.com/app",
                    status_code=200,
                    text="<html><title>App</title><body>Loaded app shell with enough text.</body></html>",
                    fetch_mode="browser",
                    metadata={
                        "fetch_mode": "browser",
                        "network_events": [
                            {
                                "url": "https://example.com/static/app.js",
                                "method": "GET",
                                "resource_type": "script",
                                "status_code": 200,
                                "failure_text": None,
                            }
                        ],
                    },
                ),
            ]
        )
    )
    result = scraper.run(
        ScrapeConfig(
            url="https://example.com/app",
            fetch_mode="browser",
            min_text_length=10,
            required_network_patterns=("/api/devices",),
            retry_policy=RetryPolicy(max_attempts=2),
        )
    )

    assert result.success is False
    assert len(result.attempts) == 2
    assert "missing required network patterns" in result.failure_reason.lower()


def test_scraper_accepts_browser_result_with_expected_network_call() -> None:
    """Browser-mode judgement should accept when the expected API call appears."""

    scraper = LearningScraper(
        fetcher=FakeFetcher(
            responses=[
                FetchResponse(
                    url="https://example.com/app",
                    status_code=200,
                    text=(
                        "<html><title>App</title><body>"
                        "This rendered app contains enough readable text and confirms device data loaded."
                        "</body></html>"
                    ),
                    fetch_mode="browser",
                    metadata={
                        "fetch_mode": "browser",
                        "network_events": [
                            {
                                "url": "https://example.com/api/devices?page=1",
                                "method": "GET",
                                "resource_type": "fetch",
                                "status_code": 200,
                                "failure_text": None,
                            }
                        ],
                    },
                )
            ]
        )
    )
    result = scraper.run(
        ScrapeConfig(
            url="https://example.com/app",
            fetch_mode="browser",
            min_text_length=30,
            required_keywords=("device",),
            required_network_patterns=("/api/devices",),
            retry_policy=RetryPolicy(max_attempts=1),
        )
    )

    assert result.success is True
    assert result.extraction is not None
    assert result.extraction.meta["fetch_mode"] == "browser"
    assert result.extraction.meta["network_events"][0]["url"].endswith("/api/devices?page=1")
