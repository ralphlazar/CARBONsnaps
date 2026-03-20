"""
CB_populate_uka_2024.py

One-time helper. Writes all 25 official 2024 UKA auction clearing prices
to the PRICE-HISTORY-MANUAL tab of the price history Google Sheet.

Source: UK ETS Authority, "Report on the functioning of the UK carbon market
for 2024", October 2025 (Table 1: Auction outcomes for the 2024 scheme year).
https://assets.publishing.service.gov.uk/media/68ee0df182670806f9d5e00f/
report-on-the-functioning-of-the-UK-carbon-market-for-2024.pdf

Schema: date | instrument_id | close | currency | source
Matches PRICE-HISTORY-AUTO and PRICE-HISTORY-MANUAL tab format.

Usage:
    python3 CB_populate_uka_2024.py              # preview
    python3 CB_populate_uka_2024.py --apply      # write to sheet

Auth: same service account key as other CB_ scripts.
Sheet ID: set via PRICE_HISTORY_SHEET_ID env var (check CB_sync_sheet.py for the ID).
"""

import os
import sys
import argparse
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# Configuration — update SHEET_ID to match your CB_sync_sheet.py value
# ---------------------------------------------------------------------------
SHEET_ID = os.environ.get("PRICE_HISTORY_SHEET_ID", "YOUR_PRICE_HISTORY_SHEET_ID_HERE")
TAB_NAME = "PRICE-HISTORY-MANUAL"
KEY_PATH = os.environ.get("REGULATORY_KEY", Path(__file__).parent / "CB_market-stats-key.json")

SOURCE = "UK ETS Authority, Report on the functioning of the UK carbon market for 2024, Oct 2025"

# All 25 auction clearing prices — from Table 1 of the official 2024 market report
UKA_2024 = [
    ("2024-01-10", 37.02),
    ("2024-01-24", 32.61),
    ("2024-02-07", 32.75),
    ("2024-02-21", 32.10),
    ("2024-03-06", 34.70),
    ("2024-03-20", 34.65),
    ("2024-04-03", 32.70),
    ("2024-04-17", 33.50),
    ("2024-05-01", 35.15),
    ("2024-05-15", 37.00),
    ("2024-05-29", 43.75),
    ("2024-06-12", 46.92),
    ("2024-06-26", 45.00),
    ("2024-07-10", 40.35),
    ("2024-07-24", 38.62),
    ("2024-08-07", 36.10),
    ("2024-08-21", 39.25),
    ("2024-09-04", 40.90),
    ("2024-09-18", 39.20),
    ("2024-10-02", 34.91),
    ("2024-10-16", 38.25),
    ("2024-10-30", 36.72),
    ("2024-11-13", 37.30),
    ("2024-11-27", 35.50),
    ("2024-12-11", 34.55),
]


def main(apply=False):
    print(f"CB_populate_uka_2024.py — {'APPLY' if apply else 'PREVIEW'} mode")
    print(f"Sheet ID: {SHEET_ID}")
    print(f"Tab: {TAB_NAME}")
    print()

    if SHEET_ID == "YOUR_PRICE_HISTORY_SHEET_ID_HERE":
        print("[FATAL] SHEET_ID not set. Open CB_sync_sheet.py, copy the sheet ID,")
        print("        and set it via: export PRICE_HISTORY_SHEET_ID=<your_id>")
        print("        Or hardcode it in this script.")
        sys.exit(1)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(str(KEY_PATH), scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    ws = sheet.worksheet(TAB_NAME)

    # Check existing rows to avoid duplicates
    existing = ws.get_all_values()
    headers = existing[0] if existing else []

    try:
        date_col = headers.index("date")
        instr_col = headers.index("instrument_id")
    except ValueError:
        # Sheet may be empty or have different header names — append anyway
        date_col = 0
        instr_col = 1

    existing_keys = set()
    for row in existing[1:]:
        if len(row) > max(date_col, instr_col):
            existing_keys.add((row[date_col].strip(), row[instr_col].strip()))

    rows_to_add = []
    for date_str, price in UKA_2024:
        key = (date_str, "UKA")
        if key in existing_keys:
            print(f"  SKIP (already exists): {date_str}  UKA  {price}")
        else:
            rows_to_add.append([date_str, "UKA", str(price), "GBP", SOURCE])
            print(f"  ADD: {date_str}  UKA  £{price}")

    print()
    print(f"Rows to add: {len(rows_to_add)}")
    print(f"Rows already present: {len(UKA_2024) - len(rows_to_add)}")
    print()

    if not rows_to_add:
        print("Nothing to do. All 2024 UKA prices already in sheet.")
        return

    if not apply:
        print("Preview only. Run with --apply to write to sheet.")
        return

    # If sheet is empty, write headers first
    if not existing:
        ws.append_row(["date", "instrument_id", "close", "currency", "source"])

    ws.append_rows(rows_to_add, value_input_option="RAW")
    print(f"Written {len(rows_to_add)} rows to {TAB_NAME}.")
    print("Done. Run CB_sync_sheet.py --apply to rebuild sparks and prices.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    main(apply=args.apply)
