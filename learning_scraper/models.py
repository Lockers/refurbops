"""Data models for the learning scraper workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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

    The keyword rules are intentionally simple so the scraper is easy to extend
    while still demonstrating how to make content quality judgements.
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
class ScrapeResult:
    """Final scraper result returned to callers."""

    success: bool
    final_url: str
    attempts: tuple[ScrapeAttempt, ...]
    extraction: ExtractionResult | None = None
    failure_reason: str | None = None
