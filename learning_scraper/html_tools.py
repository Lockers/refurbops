"""HTML parsing helpers for the learning scraper.

The parser purposely uses Python's standard library so the example stays easy to
run in a fresh environment without extra parsing dependencies.
"""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

from .models import ExtractionResult


class _ReadableHTMLParser(HTMLParser):
    """Extract a title, body text, links, and script URLs from HTML.

    Script and style bodies are ignored for readable text extraction, but script
    `src` URLs are still captured because they are useful for site inventory and
    understanding JavaScript-heavy applications.
    """

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self._skip_depth = 0
        self._in_title = False
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self._links: list[str] = []
        self._script_urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track ignored tags and collect link-like targets."""

        attr_map = dict(attrs)
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = attr_map.get("href")
            if href:
                self._links.append(urljoin(self.base_url, href))
        if tag == "script":
            src = attr_map.get("src")
            if src:
                self._script_urls.append(urljoin(self.base_url, src))

    def handle_endtag(self, tag: str) -> None:
        """Reset parser state after closing tags."""

        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        """Capture readable text content."""

        if self._skip_depth:
            return

        cleaned = " ".join(data.split())
        if not cleaned:
            return

        if self._in_title:
            self._title_parts.append(cleaned)
        else:
            self._text_parts.append(cleaned)

    def to_extraction_result(self) -> tuple[str, str, tuple[str, ...], tuple[str, ...]]:
        """Build parser output after feeding the document."""

        title = " ".join(self._title_parts).strip()
        text = " ".join(self._text_parts).strip()
        return (
            title,
            text,
            tuple(dict.fromkeys(self._links)),
            tuple(dict.fromkeys(self._script_urls)),
        )


def extract_readable_content(url: str, html: str, meta: dict | None = None) -> ExtractionResult:
    """Convert an HTML document into a normalized extraction result."""

    parser = _ReadableHTMLParser(base_url=url)
    parser.feed(html)
    title, text, links, script_urls = parser.to_extraction_result()
    enriched_meta = dict(meta or {})
    enriched_meta.setdefault("script_urls", list(script_urls))
    enriched_meta.setdefault("raw_html", html)
    return ExtractionResult(url=url, title=title, text=text, links=links, meta=enriched_meta)
