# Learning Scraper

This standalone Python package demonstrates a scraper that can:

1. fetch a page over plain HTTP
2. render a page in a real browser when JavaScript is required
3. extract readable content from HTML
4. make simple quality judgements from page text and observed network traffic
5. retry when the content looks blocked, incomplete, or too thin

## Why this is useful

It is intentionally small and inspectable, so it is a good learning base before
adding advanced features such as rotating proxies, crawl queues, domain-specific
extractors, or ML-based page classification.

## Browser support

Yes — browser-based judgement is possible. If a site relies on client-side JavaScript,
background `fetch` / XHR calls, or anti-bot pages that only appear after scripts run,
you can switch to browser mode and inspect the network activity captured during the page load.

To enable the real browser fetcher, install Playwright in your environment:

```bash
pip install playwright
playwright install chromium
```

## Example usage

Plain HTTP mode:

```bash
python -m learning_scraper.cli https://example.com --required-keyword example --min-text-length 50
```

Browser mode with network-aware judgement:

```bash
python -m learning_scraper.cli \
  https://example.com/app \
  --fetch-mode browser \
  --wait-for-selector '#app' \
  --required-network-pattern '/api/' \
  --max-failed-network-calls 1
```

## Core modules

- `models.py`: shared dataclasses and scrape configuration
- `http_client.py`: plain HTTP page fetching
- `browser_client.py`: optional Playwright-backed page rendering
- `html_tools.py`: HTML cleanup and extraction
- `judgement.py`: accept / retry / reject rules, including network-aware checks
- `runner.py`: workflow orchestration
- `cli.py`: command-line entrypoint


## Site-wide inventory

The next killer feature is a site inventory crawler that can visit multiple internal pages, summarize script bundles, surface likely API endpoints, and flag likely bot-protection vendors such as Cloudflare or hCaptcha without attempting to bypass them.

Example usage from Python:

```python
from learning_scraper import CrawlConfig, ScrapeConfig, SiteInventoryCrawler

crawler = SiteInventoryCrawler()
result = crawler.crawl(
    CrawlConfig(seed_urls=("https://example.com",), max_pages=10, max_workers=4),
    ScrapeConfig(url="https://example.com", fetch_mode="browser", min_text_length=1),
)
```

This is useful for finding site-wide API entry points and JavaScript assets before deciding whether product-by-product scraping is necessary.
