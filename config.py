"""Configuration for BDO Codex icon scraper."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent

SPREADSHEET_ID = os.getenv(
    "BDO_BARTERING_SPREADSHEET_ID",
    "1x3FanHwJMYeqroGq_Lo9PFGWW8Drwd5FwywtpLMpC-8",
)
WORKSHEET_NAME = os.getenv("BDO_BARTERING_WORKSHEET_NAME", "Item List")
CODEX_BASE_URL = os.getenv("BDO_BARTERING_CODEX_BASE_URL", "https://bdocodex.com/us/")
CODEX_ORIGIN = os.getenv("BDO_BARTERING_CODEX_ORIGIN", "https://bdocodex.com")

GOOGLE_CREDENTIALS_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(PROJECT_ROOT / "credentials" / "service_account.json"),
)

SEA_TRADE_GOOD_HEADER = "Sea Trade Good"
ICON_HEADER = "Icon"

DELAY_SECONDS_BETWEEN_ITEMS = float(os.getenv("BDO_BARTERING_DELAY_SECONDS", "2"))
