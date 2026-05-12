# BDO Bartering — Codex icon scraper

Reads item names from the Google Sheet tab **Item List** (column **Sea Trade Good**), searches [BDO Codex](https://bdocodex.com/us/), extracts each item page icon URL, and writes `=IMAGE("https://bdocodex.com/...")` into **Icon**.

## Setup

1. **Python 3.10+**

   ```bash
   cd "Automation/BDO Bartering"
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Google Cloud**

   - Create a project and enable **Google Sheets API**.
   - Create a **service account**, download the JSON key.
   - Save it as `credentials/service_account.json` (this path is gitignored).
   - Open your spreadsheet → **Share** → add the service account email with **Editor**.

3. **Environment (optional)**

   Copy `.env.example` to `.env` and adjust, or set variables directly. Defaults match the planned spreadsheet ID and sheet name.

## Run

```bash
python main.py
python main.py --force          # overwrite Icon cells that already have =IMAGE(...)
python main.py --headless       # no browser window
python main.py --delay 3        # seconds between Codex requests
```

`GOOGLE_APPLICATION_CREDENTIALS` can point to your JSON path if not using `credentials/service_account.json`.
