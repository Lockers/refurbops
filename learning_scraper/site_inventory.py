"""Site-wide inventory crawling for discovering endpoints and browser signals."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from urllib.parse import urlparse

from .discovery import detect_bot_protection_signals, discover_api_candidates
from .models import ScrapeConfig
from .runner import LearningScraper


@dataclass(slots=True)
class CrawlConfig:
    """Configuration for site-wide inventory crawling."""

    seed_urls: tuple[str, ...]
    max_pages: int = 25
    max_workers: int = 4
    same_origin_only: bool = True


@dataclass(slots=True)
class PageInventory:
    """Inventory summary captured for one crawled page."""

    url: str
    status_code: int | None
    title: str
    internal_links: tuple[str, ...]
    script_urls: tuple[str, ...]
    api_candidates: tuple[str, ...]
    bot_protection_signals: tuple[str, ...]
    success: bool
    failure_reason: str | None = None


@dataclass(slots=True)
class SiteInventoryResult:
    """Combined inventory across all visited pages."""

    pages: tuple[PageInventory, ...]
    discovered_api_candidates: tuple[str, ...]
    discovered_script_urls: tuple[str, ...]
    detected_bot_protection: tuple[str, ...]


class SiteInventoryCrawler:
    """Crawl a site breadth-first and collect high-level inventory details."""

    def __init__(self, scraper: LearningScraper | None = None) -> None:
        """Allow the page scraper to be injected for tests."""

        self._scraper = scraper or LearningScraper()

    def crawl(self, crawl_config: CrawlConfig, page_config: ScrapeConfig) -> SiteInventoryResult:
        """Visit multiple pages concurrently and summarize what the site exposes."""

        queue = list(crawl_config.seed_urls)
        visited: set[str] = set()
        page_summaries: list[PageInventory] = []
        discovered_apis: list[str] = []
        discovered_scripts: list[str] = []
        detected_protection: list[str] = []

        while queue and len(visited) < crawl_config.max_pages:
            batch_size = min(crawl_config.max_workers, crawl_config.max_pages - len(visited), len(queue))
            batch = [queue.pop(0) for _ in range(batch_size)]
            batch = [url for url in batch if url not in visited]
            if not batch:
                continue

            with ThreadPoolExecutor(max_workers=crawl_config.max_workers) as executor:
                results = list(executor.map(lambda url: self._crawl_page(url, page_config, crawl_config), batch))

            for summary, new_links in results:
                visited.add(summary.url)
                page_summaries.append(summary)
                discovered_apis.extend(summary.api_candidates)
                discovered_scripts.extend(summary.script_urls)
                detected_protection.extend(summary.bot_protection_signals)
                for link in new_links:
                    if link not in visited and link not in queue and len(visited) + len(queue) < crawl_config.max_pages:
                        queue.append(link)

        return SiteInventoryResult(
            pages=tuple(page_summaries),
            discovered_api_candidates=tuple(dict.fromkeys(discovered_apis)),
            discovered_script_urls=tuple(dict.fromkeys(discovered_scripts)),
            detected_bot_protection=tuple(dict.fromkeys(detected_protection)),
        )

    def _crawl_page(
        self,
        url: str,
        page_config: ScrapeConfig,
        crawl_config: CrawlConfig,
    ) -> tuple[PageInventory, tuple[str, ...]]:
        """Fetch one page and return its inventory plus discovered next links."""

        result = self._scraper.run(replace(page_config, url=url))
        extraction = result.extraction
        if extraction is None:
            summary = PageInventory(
                url=result.final_url,
                status_code=None,
                title="",
                internal_links=(),
                script_urls=(),
                api_candidates=(),
                bot_protection_signals=(),
                success=False,
                failure_reason=result.failure_reason,
            )
            return summary, ()

        # Use the extraction produced by the scraper so discovery can inspect the
        # normalized text, raw HTML, links, scripts, and captured metadata consistently.
        raw_html = extraction.meta.get("raw_html", "")
        bot_protection_signals = detect_bot_protection_signals(raw_html, extraction)
        api_candidates = discover_api_candidates(extraction.url, raw_html, extraction)
        internal_links = tuple(
            link
            for link in extraction.links
            if self._should_visit_link(seed_urls=crawl_config.seed_urls, candidate=link, same_origin_only=crawl_config.same_origin_only)
        )
        script_urls = tuple(extraction.meta.get("script_urls", []))

        summary = PageInventory(
            url=extraction.url,
            status_code=result.attempts[-1].status_code if result.attempts else None,
            title=extraction.title,
            internal_links=internal_links,
            script_urls=script_urls,
            api_candidates=api_candidates,
            bot_protection_signals=bot_protection_signals,
            success=result.success,
            failure_reason=result.failure_reason,
        )
        return summary, internal_links

    @staticmethod
    def _should_visit_link(seed_urls: tuple[str, ...], candidate: str, same_origin_only: bool) -> bool:
        """Limit the crawl to the same origin when requested."""

        if not same_origin_only:
            return True
        if not seed_urls:
            return False
        seed_origin = _origin(seed_urls[0])
        return _origin(candidate) == seed_origin


def _origin(url: str) -> tuple[str, str]:
    """Normalize a URL to a scheme/host pair for origin comparisons."""

    parsed = urlparse(url)
    return parsed.scheme, parsed.netloc
