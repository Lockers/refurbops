"""Learning scraper package.

This package contains a small, self-contained scraper implementation that can
fetch HTML, extract readable text, judge whether the result is usable, and retry
when the page looks incomplete or blocked.
"""

from .judgement import JudgementOutcome, PageJudgement, PageJudge, RetryReason
from .models import ExtractionResult, RetryPolicy, ScrapeConfig, ScrapeResult
from .runner import LearningScraper

__all__ = [
    "ExtractionResult",
    "JudgementOutcome",
    "LearningScraper",
    "PageJudge",
    "PageJudgement",
    "RetryPolicy",
    "RetryReason",
    "ScrapeConfig",
    "ScrapeResult",
]
