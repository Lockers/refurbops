"""Command-line interface for the learning scraper."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .models import RetryPolicy, ScrapeConfig
from .runner import LearningScraper


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(description="Run the learning scraper against a single URL.")
    parser.add_argument("url", help="Target page to fetch and evaluate.")
    parser.add_argument(
        "--required-keyword",
        action="append",
        default=[],
        dest="required_keywords",
        help="Keyword that must appear in the cleaned page text. Repeat as needed.",
    )
    parser.add_argument(
        "--forbidden-keyword",
        action="append",
        default=[],
        dest="forbidden_keywords",
        help="Keyword that should trigger a retry when present. Repeat as needed.",
    )
    parser.add_argument("--min-text-length", type=int, default=120)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--backoff-seconds", type=float, default=0.0)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    return parser


def main() -> int:
    """Parse arguments, run the scraper, and print JSON output."""

    args = build_parser().parse_args()
    config = ScrapeConfig(
        url=args.url,
        min_text_length=args.min_text_length,
        required_keywords=tuple(args.required_keywords),
        forbidden_keywords=(
            tuple(args.forbidden_keywords)
            if args.forbidden_keywords
            else ScrapeConfig(url=args.url).forbidden_keywords
        ),
        retry_policy=RetryPolicy(
            max_attempts=args.max_attempts,
            backoff_seconds=args.backoff_seconds,
        ),
        timeout_seconds=args.timeout_seconds,
    )
    result = LearningScraper().run(config)
    print(json.dumps(asdict(result), indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
