"""High-level orchestration for the learning scraper."""

from __future__ import annotations

import time

from .html_tools import extract_readable_content
from .http_client import PageFetcher
from .judgement import JudgementOutcome, PageJudge
from .models import ScrapeAttempt, ScrapeConfig, ScrapeResult


class LearningScraper:
    """Fetch pages, judge content quality, and retry when needed."""

    def __init__(self, fetcher: PageFetcher | None = None, judge: PageJudge | None = None) -> None:
        """Allow collaborators to be injected for tests or custom behavior."""

        self._fetcher = fetcher or PageFetcher()
        self._judge = judge or PageJudge()

    def run(self, config: ScrapeConfig) -> ScrapeResult:
        """Execute the scrape workflow for one URL."""

        attempts: list[ScrapeAttempt] = []
        last_failure_reason: str | None = None

        for attempt_number in range(1, config.retry_policy.max_attempts + 1):
            try:
                response = self._fetcher.fetch(config)
            except ConnectionError as exc:
                last_failure_reason = f"HTTP error: {exc}"
                attempts.append(
                    ScrapeAttempt(
                        attempt_number=attempt_number,
                        status_code=None,
                        decision=JudgementOutcome.RETRY.value,
                        reason=last_failure_reason,
                    )
                )
                if attempt_number < config.retry_policy.max_attempts:
                    self._sleep_before_retry(config)
                    continue
                return ScrapeResult(
                    success=False,
                    final_url=config.url,
                    attempts=tuple(attempts),
                    failure_reason=last_failure_reason,
                )

            if response.status_code in config.retry_policy.retry_on_statuses:
                last_failure_reason = f"Retryable status code: {response.status_code}"
                attempts.append(
                    ScrapeAttempt(
                        attempt_number=attempt_number,
                        status_code=response.status_code,
                        decision=JudgementOutcome.RETRY.value,
                        reason=last_failure_reason,
                    )
                )
                if attempt_number < config.retry_policy.max_attempts:
                    self._sleep_before_retry(config)
                    continue
                return ScrapeResult(
                    success=False,
                    final_url=response.url,
                    attempts=tuple(attempts),
                    failure_reason=last_failure_reason,
                )

            extraction = extract_readable_content(response.url, response.text)
            judgement = self._judge.judge(extraction, config)
            attempts.append(
                ScrapeAttempt(
                    attempt_number=attempt_number,
                    status_code=response.status_code,
                    decision=judgement.outcome.value,
                    reason=judgement.message,
                )
            )

            if judgement.outcome is JudgementOutcome.ACCEPT:
                return ScrapeResult(
                    success=True,
                    final_url=response.url,
                    attempts=tuple(attempts),
                    extraction=extraction,
                )

            last_failure_reason = judgement.message
            if attempt_number < config.retry_policy.max_attempts:
                self._sleep_before_retry(config)
                continue

            return ScrapeResult(
                success=False,
                final_url=response.url,
                attempts=tuple(attempts),
                extraction=extraction,
                failure_reason=last_failure_reason,
            )

        return ScrapeResult(
            success=False,
            final_url=config.url,
            attempts=tuple(attempts),
            failure_reason=last_failure_reason or "Unknown failure.",
        )

    @staticmethod
    def _sleep_before_retry(config: ScrapeConfig) -> None:
        """Apply a simple linear backoff between attempts."""

        if config.retry_policy.backoff_seconds > 0:
            time.sleep(config.retry_policy.backoff_seconds)
