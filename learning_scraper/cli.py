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
        "--fetch-mode",
        choices=("http", "browser"),
        default="http",
        help="Use plain HTTP fetching or a Playwright-backed browser.",
    )
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
    parser.add_argument(
        "--required-network-pattern",
        action="append",
        default=[],
        dest="required_network_patterns",
        help="Substring that must appear in an observed network request URL.",
    )
    parser.add_argument("--min-text-length", type=int, default=120)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--backoff-seconds", type=float, default=0.0)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--wait-until", choices=("commit", "domcontentloaded", "load", "networkidle"), default="networkidle")
    parser.add_argument("--wait-for-selector")
    parser.add_argument("--post-load-delay-seconds", type=float, default=0.0)
    parser.add_argument("--max-failed-network-calls", type=int, default=0)
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Run Playwright in headed mode when using --fetch-mode browser.",
    )
    return parser


def main() -> int:
    """Parse arguments, run the scraper, and print JSON output."""

    args = build_parser().parse_args()
    default_config = ScrapeConfig(url=args.url)
    config = ScrapeConfig(
        url=args.url,
        min_text_length=args.min_text_length,
        required_keywords=tuple(args.required_keywords),
        forbidden_keywords=(
            tuple(args.forbidden_keywords)
            if args.forbidden_keywords
            else default_config.forbidden_keywords
        ),
        retry_policy=RetryPolicy(
            max_attempts=args.max_attempts,
            backoff_seconds=args.backoff_seconds,
        ),
        timeout_seconds=args.timeout_seconds,
        fetch_mode=args.fetch_mode,
        wait_until=args.wait_until,
        wait_for_selector=args.wait_for_selector,
        post_load_delay_seconds=args.post_load_delay_seconds,
        browser_headless=not args.show_browser,
        required_network_patterns=tuple(args.required_network_patterns),
        max_failed_network_calls=args.max_failed_network_calls,
    )
    result = LearningScraper().run(config)
    print(json.dumps(asdict(result), indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
