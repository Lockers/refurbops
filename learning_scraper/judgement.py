"""Judgement rules for deciding whether scraped content is usable."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import ExtractionResult, ScrapeConfig


class JudgementOutcome(str, Enum):
    """High-level decision returned by the page judge."""

    ACCEPT = "accept"
    RETRY = "retry"
    REJECT = "reject"


class RetryReason(str, Enum):
    """Reasons that help explain why a retry or rejection occurred."""

    TOO_SHORT = "too_short"
    MISSING_KEYWORDS = "missing_keywords"
    FORBIDDEN_CONTENT = "forbidden_content"
    EMPTY_DOCUMENT = "empty_document"
    MISSING_NETWORK_CALLS = "missing_network_calls"
    TOO_MANY_FAILED_NETWORK_CALLS = "too_many_failed_network_calls"
    ACCEPTED = "accepted"


@dataclass(slots=True)
class PageJudgement:
    """Detailed judgement payload for one extraction."""

    outcome: JudgementOutcome
    reason: RetryReason
    message: str


class PageJudge:
    """Evaluate extraction quality using simple, inspectable heuristics."""

    def judge(self, extraction: ExtractionResult, config: ScrapeConfig) -> PageJudgement:
        """Return a deterministic decision for the scraped document."""

        text = extraction.text.strip()
        normalized_text = text.lower()
        network_events = extraction.meta.get("network_events", [])

        if config.required_network_patterns:
            missing_patterns = [
                pattern
                for pattern in config.required_network_patterns
                if not any(pattern.lower() in event.get("url", "").lower() for event in network_events)
            ]
            if missing_patterns:
                return PageJudgement(
                    outcome=JudgementOutcome.RETRY,
                    reason=RetryReason.MISSING_NETWORK_CALLS,
                    message=(
                        "Missing required network patterns: "
                        f"{', '.join(missing_patterns)}."
                    ),
                )

        failed_network_calls = [event for event in network_events if event.get("failure_text")]
        if len(failed_network_calls) > config.max_failed_network_calls:
            return PageJudgement(
                outcome=JudgementOutcome.RETRY,
                reason=RetryReason.TOO_MANY_FAILED_NETWORK_CALLS,
                message=(
                    "Observed too many failed network calls: "
                    f"{len(failed_network_calls)} > {config.max_failed_network_calls}."
                ),
            )

        if not normalized_text:
            return PageJudgement(
                outcome=JudgementOutcome.RETRY,
                reason=RetryReason.EMPTY_DOCUMENT,
                message="The document was empty after HTML cleanup.",
            )

        for keyword in config.forbidden_keywords:
            if keyword.lower() in normalized_text:
                return PageJudgement(
                    outcome=JudgementOutcome.RETRY,
                    reason=RetryReason.FORBIDDEN_CONTENT,
                    message=f"Found forbidden keyword: {keyword}.",
                )

        if len(text) < config.min_text_length:
            return PageJudgement(
                outcome=JudgementOutcome.RETRY,
                reason=RetryReason.TOO_SHORT,
                message=(
                    f"Readable text was only {len(text)} characters, shorter than "
                    f"the configured minimum of {config.min_text_length}."
                ),
            )

        missing_keywords = [
            keyword for keyword in config.required_keywords if keyword.lower() not in normalized_text
        ]
        if missing_keywords:
            return PageJudgement(
                outcome=JudgementOutcome.RETRY,
                reason=RetryReason.MISSING_KEYWORDS,
                message=f"Missing required keywords: {', '.join(missing_keywords)}.",
            )

        return PageJudgement(
            outcome=JudgementOutcome.ACCEPT,
            reason=RetryReason.ACCEPTED,
            message="The page passed all judgement rules.",
        )
