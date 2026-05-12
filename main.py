"""
BDO Codex icon scraper: read Sea Trade Good from Google Sheets, write Icon =IMAGE(...).
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from playwright.sync_api import sync_playwright

from codex_scraper import scrape_icon_url_for_item
from config import DELAY_SECONDS_BETWEEN_ITEMS
from sheets_client import batch_write_icon_formulas, load_item_rows

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_FLUSH_EVERY = 15


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill Icon column from BDO Codex search.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite cells that already contain =IMAGE(...).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser without a window (default: headed).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help=f"Seconds between Codex requests (default: {DELAY_SECONDS_BETWEEN_ITEMS}).",
    )
    args = parser.parse_args()

    delay = args.delay if args.delay is not None else DELAY_SECONDS_BETWEEN_ITEMS

    try:
        ws, _df, rows = load_item_rows(force=args.force)
    except Exception as e:
        logger.error("%s", e)
        return 1

    if not rows:
        logger.info("Nothing to process.")
        return 0

    pending: list[tuple[int, str, str]] = []

    def flush() -> None:
        if pending:
            batch_write_icon_formulas(ws, pending)
            pending.clear()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=args.headless)
            context = browser.new_context()
            page = context.new_page()
            try:
                for i, item in enumerate(rows):
                    logger.info(
                        "(%s/%s) %s",
                        i + 1,
                        len(rows),
                        item.sea_trade_good,
                    )
                    url = scrape_icon_url_for_item(page, context, item.sea_trade_good)
                    if url:
                        pending.append(
                            (item.sheet_row_1based, item.icon_col_letters, url)
                        )
                    if len(pending) >= BATCH_FLUSH_EVERY:
                        flush()
                    time.sleep(delay)
            finally:
                browser.close()
    except KeyboardInterrupt:
        logger.warning("Interrupted; flushing pending updates.")
        flush()
        return 130

    flush()
    logger.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
