"""Google Sheets read/write for Item List."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

from config import (
    GOOGLE_CREDENTIALS_PATH,
    ICON_HEADER,
    SEA_TRADE_GOOD_HEADER,
    SPREADSHEET_ID,
    WORKSHEET_NAME,
)

logger = logging.getLogger(__name__)

SCOPES = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
)



def col_index_to_letters(index_zero_based: int) -> str:
    """Convert 0-based column index to A1 letters (A, B, ..., Z, AA, ...)."""
    n = index_zero_based + 1
    letters = ""
    while n:
        n, remainder = divmod(n - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _has_image_formula(value: str) -> bool:
    if not value or not isinstance(value, str):
        return False
    return bool(re.match(r"^\s*=\s*IMAGE\s*\(", value.strip(), re.IGNORECASE))


@dataclass
class ItemRow:
    """One sheet row to process."""

    sheet_row_1based: int
    sea_trade_good: str
    icon_col_letters: str


def authorize_gspread(credentials_path: str | Path | None = None) -> gspread.Client:
    path = Path(credentials_path or GOOGLE_CREDENTIALS_PATH)
    if not path.is_file():
        raise FileNotFoundError(
            f"Service account JSON not found at {path}. "
            "Place credentials/service_account.json or set GOOGLE_APPLICATION_CREDENTIALS."
        )
    creds = Credentials.from_service_account_file(str(path), scopes=list(SCOPES))
    return gspread.authorize(creds)


def load_item_rows(force: bool = False) -> tuple[gspread.Worksheet, pd.DataFrame, list[ItemRow]]:
    """
    Load all values from Item List; return worksheet, full DataFrame, and rows to scrape.
    Rows to scrape: non-empty Sea Trade Good; skip Icon if already IMAGE(...) unless force.
    """
    gc = authorize_gspread()
    sh = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = sh.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound as e:
        raise RuntimeError(f'Worksheet "{WORKSHEET_NAME}" not found in spreadsheet.') from e

    rows = ws.get_all_values(value_render_option="FORMULA")
    if not rows:
        return ws, pd.DataFrame(), []

    headers = [h.strip() for h in rows[0]]
    try:
        sea_idx = headers.index(SEA_TRADE_GOOD_HEADER)
        icon_idx = headers.index(ICON_HEADER)
    except ValueError as e:
        raise RuntimeError(
            f'Headers must include "{SEA_TRADE_GOOD_HEADER}" and "{ICON_HEADER}". Found: {headers}'
        ) from e

    data_rows = rows[1:]
    width = len(headers)
    padded: list[list[str]] = []
    for r in data_rows:
        row = list(r) + [""] * (width - len(r))
        padded.append(row[:width])

    df = pd.DataFrame(padded, columns=headers)

    icon_letters = col_index_to_letters(icon_idx)
    to_process: list[ItemRow] = []

    for i, row_list in enumerate(data_rows):
        sheet_row = i + 2  # 1 header + 1-based
        sea = row_list[sea_idx].strip() if sea_idx < len(row_list) else ""
        if not sea:
            continue
        icon_cell = row_list[icon_idx].strip() if icon_idx < len(row_list) else ""
        if icon_cell and _has_image_formula(icon_cell) and not force:
            logger.info("Skip row %s (already has IMAGE): %s", sheet_row, sea[:50])
            continue
        to_process.append(
            ItemRow(sheet_row_1based=sheet_row, sea_trade_good=sea, icon_col_letters=icon_letters)
        )

    return ws, df, to_process


def batch_write_icon_formulas(
    worksheet: gspread.Worksheet,
    updates: list[tuple[int, str, str]],
) -> None:
    """
    updates: list of (sheet_row_1based, icon_col_letters, full_icon_url)
    Writes =IMAGE("url") with USER_ENTERED.
    """
    if not updates:
        return

    data = [
        {
            "range": f"{col_letters}{row_num}",
            "values": [[f'=IMAGE("{url}")']],
        }
        for row_num, col_letters, url in updates
    ]
    worksheet.batch_update(data, value_input_option="USER_ENTERED")
    logger.info("Batch updated %s Icon cells.", len(data))
