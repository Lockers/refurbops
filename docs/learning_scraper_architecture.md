# Learning Scraper Architecture

## Purpose

This document describes the standalone learning scraper added to the repository.
It is intentionally separate from the existing RefurbOps backend so the scraper
can be used as a teaching example without coupling it to the product codebase.

## Design goals

- keep the implementation runnable with minimal dependencies
- show a clear scrape -> judge -> retry workflow
- keep logic modular so future steps can replace any layer independently
- make retry decisions explainable rather than hidden in opaque heuristics

## Flow

1. `PageFetcher` downloads the target page.
2. `extract_readable_content` removes script/style noise and normalizes visible text.
3. `PageJudge` decides whether the page is acceptable, suspicious, or too thin.
4. `LearningScraper` retries when the HTTP response or the extracted content suggests retrying.

## Retry strategy

The initial version uses bounded retries with optional linear backoff. Retries are triggered by:

- common transient HTTP statuses such as `429`, `500`, and `503`
- empty or very short documents after extraction
- forbidden phrases that often indicate bot walls or temporary blocking
- missing required keywords when the caller expects a specific page topic

## Future extensions

Potential next steps include:

- browser-backed rendering for JavaScript-heavy targets
- proxy rotation and rate-limit awareness
- persistent crawl queues
- structured extraction rules per domain
- ML-based content classification
