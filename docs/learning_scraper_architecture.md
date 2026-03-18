# Learning Scraper Architecture

## Purpose

This document describes the standalone learning scraper added to the repository.
It is intentionally separate from the existing RefurbOps backend so the scraper
can be used as a teaching example without coupling it to the product codebase.

## Design goals

- keep the implementation runnable with minimal dependencies in HTTP mode
- support a browser-backed mode for JavaScript-heavy sites
- show a clear scrape -> judge -> retry workflow
- keep logic modular so future steps can replace any layer independently
- make retry decisions explainable rather than hidden in opaque heuristics

## Flow

1. `PageFetcher` downloads the target page in plain HTTP mode.
2. `BrowserFetcher` can alternatively load the page in Chromium through Playwright.
3. `extract_readable_content` removes script/style noise and normalizes visible text.
4. `PageJudge` decides whether the page is acceptable, suspicious, or too thin.
5. `LearningScraper` retries when the HTTP response, rendered content, or network activity suggests retrying.

## Browser-based judgement

Browser mode is meant for pages that require JavaScript execution or background API calls.
When enabled, the scraper can:

- wait for `load`, `domcontentloaded`, `networkidle`, or `commit`
- optionally wait for a selector that indicates the app finished rendering
- record network responses and request failures during page load
- use that network data as part of the acceptance / retry decision

This makes it practical to judge cases such as:

- a page shell renders but the expected `/api/` data call never happened
- a JavaScript app loaded, but several important requests failed
- the HTML is short because the real content is supposed to appear after hydration

## Retry strategy

The current version uses bounded retries with optional linear backoff. Retries are triggered by:

- common transient HTTP statuses such as `429`, `500`, and `503`
- empty or very short documents after extraction
- forbidden phrases that often indicate bot walls or temporary blocking
- missing required keywords when the caller expects a specific page topic
- missing required network request patterns in browser mode
- too many failed browser network calls

## Future extensions

Potential next steps include:

- capturing console errors and JavaScript exceptions
- browser screenshots or HTML snapshots on failed attempts
- proxy rotation and rate-limit awareness
- persistent crawl queues
- structured extraction rules per domain
- ML-based content classification
