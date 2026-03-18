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
