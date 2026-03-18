"""Data models for the learning scraper workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


FetchMode = Literal["http", "browser"]
WaitUntil = Literal["commit", "domcontentloaded", "load", "networkidle"]


@dataclass(slots=True)
class RetryPolicy:
    """Configuration for bounded retry behavior.

    Attributes:
        max_attempts: Maximum number of fetch attempts for one scrape job.
        backoff_seconds: Base delay applied before each retry.
        retry_on_statuses: HTTP statuses that should trigger another attempt.
    """

    max_attempts: int = 3
    backoff_seconds: float = 0.0
    retry_on_statuses: tuple[int, ...] = (408, 425, 429, 500, 502, 503, 504)


@dataclass(slots=True)
class ScrapeConfig:
    """User-facing configuration for a scrape run.

    The browser-related fields are optional so the learning project can start in
    plain HTTP mode and graduate to full browser rendering when a target site
    depends on JavaScript or background network activity.
    """

    url: str
    min_text_length: int = 120
    required_keywords: tuple[str, ...] = ()
    forbidden_keywords: tuple[str, ...] = (
        "captcha",
        "access denied",
        "robot or human",
        "temporarily unavailable",
    )
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    timeout_seconds: float = 10.0
    user_agent: str = "LearningScraper/1.0"
    fetch_mode: FetchMode = "http"
    wait_until: WaitUntil = "networkidle"
    wait_for_selector: str | None = None
    post_load_delay_seconds: float = 0.0
    browser_headless: bool = True
    required_network_patterns: tuple[str, ...] = ()
    max_failed_network_calls: int = 0


@dataclass(slots=True)
class NetworkEvent:
    """Observed browser network activity for a single request/response cycle."""

    url: str
    method: str
    resource_type: str
    status_code: int | None = None
    failure_text: str | None = None


@dataclass(slots=True)
class ExtractionResult:
    """Normalized output from the HTML extraction stage."""

    url: str
    title: str
    text: str
    links: tuple[str, ...]
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScrapeAttempt:
    """Single attempt metadata recorded during orchestration."""

    attempt_number: int
    status_code: int | None
    decision: str
    reason: str


@dataclass(slots=True)
class FetchResponse:
    """Normalized response returned by any fetch implementation."""

    url: str
    status_code: int
    text: str
    fetch_mode: FetchMode = "http"
    network_events: tuple[NetworkEvent, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScrapeResult:
    """Final scraper result returned to callers."""

    success: bool
    final_url: str
    attempts: tuple[ScrapeAttempt, ...]
    extraction: ExtractionResult | None = None
    failure_reason: str | None = None
