"""Playwright: search BDO Codex and extract item icon URL."""

from __future__ import annotations

import logging
import re
import time
from urllib.parse import urljoin

from playwright.sync_api import BrowserContext, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config import CODEX_BASE_URL, CODEX_ORIGIN

logger = logging.getLogger(__name__)

ITEM_URL_PATTERN = re.compile(r"/item/\d+")

SEARCH_INPUT = "#searchfield"
SUGGESTION_SELECTOR = ".tt-menu .tt-suggestion"


def normalize_icon_url(src: str | None, origin: str = CODEX_ORIGIN) -> str | None:
    if not src or not isinstance(src, str):
        return None
    src = src.strip()
    if not src:
        return None
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        return urljoin(origin.rstrip("/") + "/", src.lstrip("/"))
    if src.startswith("http"):
        return src
    return urljoin(origin.rstrip("/") + "/", src)


def extract_icon_src_from_page(page: Page) -> str | None:
    selectors = (
        "td.icon_cell img.item_icon",
        "img.item_icon",
        ".icon_cell img[src]",
    )
    for sel in selectors:
        loc = page.locator(sel)
        try:
            if loc.count() == 0:
                continue
            src = loc.first.get_attribute("src")
            out = normalize_icon_url(src)
            if out:
                return out
        except PlaywrightTimeoutError:
            continue
    return None


def _click_best_suggestion(page: Page, item_name: str) -> bool:
    """Return True if a suggestion was clicked."""
    needle = item_name.strip().lower()
    suggestions = page.locator(SUGGESTION_SELECTOR)
    try:
        suggestions.first.wait_for(state="visible", timeout=8000)
    except PlaywrightTimeoutError:
        return False

    n = suggestions.count()
    if n == 0:
        return False

    texts: list[tuple[int, str]] = []
    for i in range(n):
        cell = suggestions.nth(i)
        try:
            text = cell.inner_text(timeout=3000).strip().lower()
        except PlaywrightTimeoutError:
            continue
        texts.append((i, text))

    for i, text in texts:
        if text == needle:
            suggestions.nth(i).click()
            return True

    for i, text in texts:
        if needle in text:
            suggestions.nth(i).click()
            return True

    suggestions.first.click()
    return True


def _wait_and_pick_suggestion(page: Page, item_name: str) -> None:
    page.wait_for_selector(SEARCH_INPUT, state="visible", timeout=20000)
    search = page.locator(SEARCH_INPUT)
    search.click()
    search.fill("")
    search.fill(item_name)
    time.sleep(0.45)

    if _click_best_suggestion(page, item_name):
        return

    for alt in (".twitter-typeahead .tt-suggestion", "[class*='tt-suggestion']"):
        suggestions = page.locator(alt)
        try:
            if suggestions.count() > 0 and suggestions.first.is_visible():
                suggestions.first.click()
                return
        except PlaywrightTimeoutError:
            continue

    logger.warning("No dropdown suggestion; pressing Enter for %r", item_name)
    page.keyboard.press("Enter")


def open_item_page_from_search(
    page: Page,
    context: BrowserContext,
    item_name: str,
    navigation_timeout_ms: int = 35000,
) -> Page | None:
    page.goto(CODEX_BASE_URL, wait_until="domcontentloaded", timeout=navigation_timeout_ms)

    item_page: Page | None = None
    try:
        with context.expect_page(timeout=15000) as new_page_info:
            _wait_and_pick_suggestion(page, item_name)
        item_page = new_page_info.value
        item_page.wait_for_load_state("domcontentloaded", timeout=navigation_timeout_ms)
    except PlaywrightTimeoutError:
        try:
            page.wait_for_url(re.compile(r".*/item/\d+.*"), timeout=navigation_timeout_ms)
            item_page = page
        except PlaywrightTimeoutError:
            logger.error("No item page navigation for %r", item_name)
            return None

    if item_page is None:
        return None

    url = item_page.url or ""
    if not ITEM_URL_PATTERN.search(url):
        logger.error("Opened URL is not an item page: %s", url)
        if item_page is not page:
            item_page.close()
        return None

    return item_page


def scrape_icon_url_for_item(
    page: Page,
    context: BrowserContext,
    item_name: str,
) -> str | None:
    item_page = open_item_page_from_search(page, context, item_name)
    if not item_page:
        return None
    try:
        item_page.wait_for_selector(
            "td.icon_cell img.item_icon, img.item_icon",
            state="attached",
            timeout=20000,
        )
        url = extract_icon_src_from_page(item_page)
        if url:
            logger.info("Icon for %r -> %s", item_name, url)
        else:
            logger.error("No icon src on page for %r", item_name)
        return url
    finally:
        if item_page is not page:
            item_page.close()
