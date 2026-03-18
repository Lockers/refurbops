"""Discovery helpers for site-wide inventory and endpoint analysis."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from .models import ExtractionResult

_API_PATTERN = re.compile(r"(?:https?://[^\"'\s>]+|/api/[^\"'\s>]+|/graphql[^\"'\s>]*)")

_BOT_SIGNAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "cloudflare": ("cloudflare", "cf-ray", "challenge-platform", "__cf_chl_"),
    "cloudflare_turnstile": ("challenges.cloudflare.com/turnstile", "cf-turnstile"),
    "hcaptcha": ("hcaptcha", "js.hcaptcha.com"),
    "recaptcha": ("recaptcha", "gstatic.com/recaptcha"),
    "perimeterx": ("perimeterx", "px-captcha"),
    "datadome": ("datadome",),
    "akamai": ("akamai", "_abck", "bm_sv"),
}


def discover_api_candidates(page_url: str, html: str, extraction: ExtractionResult) -> tuple[str, ...]:
    """Find likely API endpoints from HTML content and observed network traffic."""

    candidates: list[str] = []
    for event in extraction.meta.get("network_events", []):
        url = event.get("url", "")
        if _looks_like_api(url):
            candidates.append(url)

    for match in _API_PATTERN.findall(html):
        if match.startswith("/"):
            parsed = urlparse(page_url)
            match = f"{parsed.scheme}://{parsed.netloc}{match}"
        if _looks_like_api(match):
            candidates.append(match)

    return tuple(dict.fromkeys(candidates))


def detect_bot_protection_signals(html: str, extraction: ExtractionResult) -> tuple[str, ...]:
    """Identify likely bot-protection vendors or challenge pages without bypassing them."""

    haystacks = [html.lower(), extraction.text.lower(), extraction.title.lower()]
    haystacks.extend(url.lower() for url in extraction.meta.get("script_urls", []))
    haystacks.extend(event.get("url", "").lower() for event in extraction.meta.get("network_events", []))

    detected: list[str] = []
    for label, patterns in _BOT_SIGNAL_PATTERNS.items():
        if any(pattern in haystack for haystack in haystacks for pattern in patterns):
            detected.append(label)

    return tuple(detected)


def _looks_like_api(url: str) -> bool:
    """Use a conservative heuristic to classify likely API endpoints."""

    lowered = url.lower()
    return any(marker in lowered for marker in ("/api/", "/graphql", "application/json", "rest"))
