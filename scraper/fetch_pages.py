from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    html: str
    fetched_at: str
    error: Optional[str] = None


def fetch_page(url: str, timeout: int = 30) -> FetchResult:
    """
    Fetch a page using requests.
    If a page is heavily JavaScript-rendered, add Playwright later.
    """
    fetched_at = datetime.now(timezone.utc).isoformat()

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        return FetchResult(
            url=url,
            final_url=str(response.url),
            status_code=response.status_code,
            html=response.text,
            fetched_at=fetched_at,
            error=None,
        )
    except Exception as exc:
        return FetchResult(
            url=url,
            final_url=url,
            status_code=0,
            html="",
            fetched_at=fetched_at,
            error=str(exc),
        )


def fetch_page_with_playwright(url: str, timeout: int = 30) -> FetchResult:
    """
    Optional browser-based fetch for JS-heavy pages.

    Requires:
        pip install playwright
        playwright install
    """
    fetched_at = datetime.now(timezone.utc).isoformat()

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return FetchResult(
            url=url,
            final_url=url,
            status_code=0,
            html="",
            fetched_at=fetched_at,
            error=f"Playwright not available: {exc}",
        )

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            html = page.content()
            final_url = page.url
            browser.close()

        return FetchResult(
            url=url,
            final_url=final_url,
            status_code=200,
            html=html,
            fetched_at=fetched_at,
            error=None,
        )
    except Exception as exc:
        return FetchResult(
            url=url,
            final_url=url,
            status_code=0,
            html="",
            fetched_at=fetched_at,
            error=str(exc),
        )