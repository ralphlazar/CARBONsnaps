"""
CB_fetch_market_data.py

Fetch layer script. Contacts external APIs (yfinance) and writes 36 months of
daily close prices to the PRICE-HISTORY-AUTO tab in the REGULATORY-TRACKER
Google Sheet.

Pipeline architecture rule: this script NEVER reads or writes CB_data.json.
It only writes to Google Sheets. The sync layer (CB_sync_sheet.py) is
responsible for reading the sheet and writing to CB_data.json.

Usage:
    python3 CB_fetch_market_data.py              # preview mode — prints what
                                                 # would be written, no writes
    python3 CB_fetch_market_data.py --apply      # writes to Google Sheets

Auth: service account key at path set by CB_MARKET_KEY env var,
      or falls back to CB_market-stats-key.json in the script directory.

Sheet ID: set via REGULATORY_SHEET_ID env var, or hardcode SHEET_ID below.

To add a new yfinance instrument later, add an entry to YFINANCE_INSTRUMENTS.
"""

import os
import sys
import argparse
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SHEET_ID  = os.environ.get("REGULATORY_SHEET_ID", "1Tvg30ZkRbomed3zVIx42DLcAAYVK9q50m4yX-hJwu68")
TAB_NAME  = "PRICE-HISTORY-AUTO"
KEY_PATH  = os.environ.get("CB_MARKET_KEY",
                           Path(__file__).parent / "CB_market-stats-key.json")

HISTORY_MONTHS = 36

# Each entry: id matches CB_data.json instrument ID exactly.
# ticker is the yfinance symbol.
# Add entries here as new free data sources become available.
YFINANCE_INSTRUMENTS = [
    {"id": "EUA", "ticker": "CO2.L", "currency": "GBP"},  # SparkChange Physical Carbon EUA ETF (LSE). EUA futures not available via yfinance.
]

TAB_HEADERS = ["date", "instrument_id", "close", "currency", "source"]

# ---------------------------------------------------------------------------
# Sheet connection
# ---------------------------------------------------------------------------

def connect_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(str(KEY_PATH), scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


def get_or_create_tab(sheet, tab_name, headers):
    try:
        ws = sheet.worksheet(tab_name)
        print(f"  Found existing tab '{tab_name}'")
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=tab_name, rows=5000, cols=len(headers))
        ws.append_row(headers)
        print(f"  Created new tab '{tab_name}'")
    return ws


# ---------------------------------------------------------------------------
# Fetch from yfinance
# ---------------------------------------------------------------------------

def fetch_yfinance(instrument_id, ticker, currency):
    """
    Download daily closes for the given ticker via yfinance.
    Returns a list of row dicts ready for the sheet, or [] on failure.

    Handles the multi-level column header introduced in yfinance 0.2+.
    """
    end   = date.today()
    # Fetch slightly more than 36 months to ensure we always have a full window
    start = end - timedelta(days=HISTORY_MONTHS * 31)

    print(f"  Fetching {instrument_id} ({ticker})...")
    try:
        df = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
    except Exception as exc:
        print(f"  [ERROR] yfinance download failed for {ticker}: {exc}")
        return []

    if df is None or df.empty:
        print(f"  [WARN] No data returned for {ticker}. Ticker may have changed.")
        return []

    # yfinance >= 0.2 returns MultiIndex columns when auto_adjust=True.
    # Flatten to single-level so we can reliably access "Close".
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if "Close" not in df.columns:
        print(f"  [ERROR] 'Close' column not found for {ticker}. Columns: {list(df.columns)}")
        return []

    # Trim to strictly within the 36-month window
    cutoff = end - timedelta(days=HISTORY_MONTHS * 30)
    df = df[df.index.date >= cutoff]

    # Drop any NaN closes (e.g. first/last row artefacts)
    df = df.dropna(subset=["Close"])

    if df.empty:
        print(f"  [WARN] No valid close prices after filtering for {ticker}.")
        return []

    source = f"yfinance:{ticker}"
    rows = []
    for ts, row in df.iterrows():
        close_val = row["Close"]
        # Ensure scalar (in case yfinance returns a Series element)
        if hasattr(close_val, "item"):
            close_val = close_val.item()
        rows.append({
            "date":          ts.strftime("%Y-%m-%d"),
            "instrument_id": instrument_id,
            "close":         round(float(close_val), 4),
            "currency":      currency,
            "source":        source,
        })

    first, last = rows[0]["date"], rows[-1]["date"]
    print(f"  {len(rows)} trading days fetched ({first} to {last})")
    return rows


# ---------------------------------------------------------------------------
# Write to sheet
# ---------------------------------------------------------------------------

def write_to_sheet(ws, new_rows, instrument_id):
    """
    Replace all rows for instrument_id in the sheet with new_rows.
    Rows for other instruments are left untouched.
    Header row is always preserved.

    Clear-and-rewrite strategy: consistent with the spark array rule (always
    rebuilt from source, never rolled forward one point at a time).
    """
    print(f"  Reading existing sheet data...")
    existing = ws.get_all_values()

    if not existing:
        # Sheet is empty (just created without header) — write header + rows
        header = TAB_HEADERS
        kept_rows = []
    else:
        header = existing[0]
        # Validate header has instrument_id column
        if "instrument_id" not in header:
            print(f"  [ERROR] Sheet header missing 'instrument_id'. Aborting write.")
            return
        id_col = header.index("instrument_id")
        # Keep rows that belong to OTHER instruments
        kept_rows = [
            row for row in existing[1:]
            if len(row) > id_col and row[id_col] != instrument_id
        ]

    # Convert new_rows dicts to lists in header order
    def row_to_list(r):
        return [r.get(h, "") for h in header]

    new_lists = [row_to_list(r) for r in new_rows]

    # Combine: other-instrument rows first, then new rows, sorted by
    # (instrument_id, date) for readability
    all_data = kept_rows + new_lists
    date_col = header.index("date") if "date" in header else 0
    id_col   = header.index("instrument_id") if "instrument_id" in header else 1
    all_data.sort(key=lambda r: (r[id_col] if len(r) > id_col else "",
                                 r[date_col] if len(r) > date_col else ""))

    total_rows = len(all_data)
    ws.clear()
    ws.update([header] + all_data)
    print(f"  Sheet written: {total_rows} data rows total "
          f"({len(new_lists)} for {instrument_id})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fetch(apply=False):
    today = date.today()
    print(f"CB_fetch_market_data.py — {'APPLY' if apply else 'PREVIEW'} mode")
    print(f"Date:    {today}")
    print(f"History: {HISTORY_MONTHS} months")
    print(f"Sheet:   {SHEET_ID}")
    print()

    # --- Fetch from external APIs ---
    all_fetched = {}

    for cfg in YFINANCE_INSTRUMENTS:
        rows = fetch_yfinance(cfg["id"], cfg["ticker"], cfg["currency"])
        if rows:
            all_fetched[cfg["id"]] = rows
        print()

    if not all_fetched:
        print("[FATAL] No data fetched from any source. Nothing to write.")
        sys.exit(1)

    # --- Summary ---
    print("Fetch summary:")
    for iid, rows in all_fetched.items():
        print(f"  {iid}: {len(rows)} rows  ({rows[0]['date']} to {rows[-1]['date']})")
    print()

    if not apply:
        print("Preview only. Run with --apply to write to Google Sheets.")
        return

    # --- Connect and write ---
    print("Connecting to Google Sheets...")
    try:
        sheet = connect_sheet()
    except Exception as exc:
        print(f"[FATAL] Could not connect to Google Sheets: {exc}")
        sys.exit(1)

    ws = get_or_create_tab(sheet, TAB_NAME, TAB_HEADERS)
    print()

    for instrument_id, rows in all_fetched.items():
        print(f"Writing {instrument_id} to '{TAB_NAME}'...")
        write_to_sheet(ws, rows, instrument_id)
        print()

    print("Done.")
    print()
    print("Next step: run CB_sync_sheet.py to push prices and sparks into CB_data.json.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch carbon market price history from yfinance and write to Google Sheets."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write to Google Sheets (default is preview mode, no writes).",
    )
    args = parser.parse_args()
    fetch(apply=args.apply)
