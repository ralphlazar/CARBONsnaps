"""
CB_sync_sheet.py

Sync layer script. Reads PRICE-HISTORY-AUTO and PRICE-HISTORY-MANUAL tabs from
the REGULATORY-TRACKER Google Sheet, and writes spark arrays, current prices,
and change fields into CB_data.json.

Pipeline architecture rule: this script NEVER contacts any external API.
It reads exclusively from Google Sheets via gspread and writes to CB_data.json.

Write-path separation: this script only touches the following fields per
instrument — price, change_1w, change_1m, change_3m, spark, last_updated.
It does NOT touch story, value_at_generation, regulatory_signal,
regulatory_note, or any other field.

value_at_generation: this script warns when a price change would cause a
value_at_generation mismatch, but does NOT update value_at_generation.
That field is owned exclusively by CB_update_stories.py. After running this
script with --apply, run CB_update_stories.py before CB_build.py, or the
build will fail on the mismatch guard.

Merge rule: PRICE-HISTORY-MANUAL wins over PRICE-HISTORY-AUTO on the same
instrument + date. Use the manual tab to correct or override any auto row.

Usage:
    python3 CB_sync_sheet.py              # preview mode — prints proposed
                                          # changes, no writes
    python3 CB_sync_sheet.py --apply      # writes to CB_data.json

Auth: service account key at path set by CB_MARKET_KEY env var,
      or falls back to CB_market-stats-key.json in the script directory.

Sheet ID: set via REGULATORY_SHEET_ID env var, or hardcode SHEET_ID below.
"""

import os
import sys
import json
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SHEET_ID       = os.environ.get("REGULATORY_SHEET_ID", "1Tvg30ZkRbomed3zVIx42DLcAAYVK9q50m4yX-hJwu68")
AUTO_TAB_NAME  = "PRICE-HISTORY-AUTO"
MANUAL_TAB_NAME = "PRICE-HISTORY-MANUAL"
DATA_JSON_PATH = Path(__file__).parent / "CB_data.json"
KEY_PATH       = os.environ.get("CB_MARKET_KEY",
                                Path(__file__).parent / "CB_market-stats-key.json")

# Columns required in both tabs (source column is optional but validated if present)
REQUIRED_HEADERS = ["date", "instrument_id", "close", "currency"]

# Price units for display — used when updating price_unit if missing
PRICE_UNITS = {
    "EUA":    "EUR/tonne",
    "CCA":    "USD/tonne",
    "UKA":    "GBP/tonne",
    "CORSIA": "USD/tonne",
    "LCFS":   "USD/credit",
    "RIN":    "USD/RIN",
    "45Z":    "USD/gallon",
    "VCM":    "USD/tonne (nature-based avg)",
}

# ---------------------------------------------------------------------------
# Sheet connection
# ---------------------------------------------------------------------------

def connect_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file(str(KEY_PATH), scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


# ---------------------------------------------------------------------------
# Read a price history tab
# ---------------------------------------------------------------------------

def read_tab(sheet, tab_name):
    """
    Read a price history tab and return a list of validated row dicts.
    Each dict has: date (str YYYY-MM-DD), instrument_id (str), close (float),
    currency (str), source (str or None).

    Rows with bad dates or non-numeric closes are skipped with a warning.
    """
    try:
        ws = sheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        print(f"  [WARN] Tab '{tab_name}' not found. Skipping.")
        return []

    all_values = ws.get_all_values()
    if not all_values:
        print(f"  [WARN] Tab '{tab_name}' is empty.")
        return []

    headers = all_values[0]

    # Check required headers
    missing = [h for h in REQUIRED_HEADERS if h not in headers]
    if missing:
        print(f"  [ERROR] Tab '{tab_name}' is missing required columns: {missing}. Skipping tab.")
        return []

    rows = []
    skipped = 0

    for i, raw in enumerate(all_values[1:], start=2):
        # Pad short rows
        while len(raw) < len(headers):
            raw.append("")
        record = {headers[j]: raw[j].strip() for j in range(len(headers))}

        # Skip blank rows
        if not any(record.values()):
            continue

        # Validate date
        date_str = record.get("date", "")
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"  [WARN] {tab_name} row {i}: invalid date '{date_str}'. Skipped.")
            skipped += 1
            continue

        # Validate instrument_id
        if not record.get("instrument_id"):
            print(f"  [WARN] {tab_name} row {i}: missing instrument_id. Skipped.")
            skipped += 1
            continue

        # Validate close
        try:
            close_val = float(record["close"])
        except (ValueError, TypeError):
            print(f"  [WARN] {tab_name} row {i} ({record.get('instrument_id')}): "
                  f"invalid close '{record.get('close')}'. Skipped.")
            skipped += 1
            continue

        rows.append({
            "date":          date_str,
            "instrument_id": record["instrument_id"],
            "close":         close_val,
            "currency":      record.get("currency", ""),
            "source":        record.get("source", None),
        })

    label = f"  {tab_name}: {len(rows)} valid rows"
    if skipped:
        label += f", {skipped} skipped"
    print(label)
    return rows


# ---------------------------------------------------------------------------
# Build per-instrument history
# ---------------------------------------------------------------------------

def build_history(auto_rows, manual_rows):
    """
    Merge auto and manual rows into per-instrument price histories.
    Manual wins over auto on the same instrument + date.
    Returns: dict of instrument_id -> list of {date, close} sorted ascending.
    """
    # Process auto first, then manual (manual writes last, overwriting on clash)
    by_instrument = {}

    for row in auto_rows + manual_rows:
        iid = row["instrument_id"]
        if iid not in by_instrument:
            by_instrument[iid] = {}
        by_instrument[iid][row["date"]] = row["close"]

    # Convert to sorted lists
    result = {}
    for iid, date_map in by_instrument.items():
        sorted_pairs = sorted(date_map.items())  # sort by date string (YYYY-MM-DD sorts correctly)
        result[iid] = [{"date": d, "close": c} for d, c in sorted_pairs]

    return result


# ---------------------------------------------------------------------------
# Price and change computation
# ---------------------------------------------------------------------------

def find_close_on_or_before(history, target_date_str):
    """
    Return the close price for the most recent entry on or before target_date_str.
    history is sorted ascending. Returns float or None.
    """
    best = None
    for entry in history:
        if entry["date"] <= target_date_str:
            best = entry["close"]
        else:
            break
    return best


def fmt_change(latest, past):
    """Calculate '+1.2%' / '-3.4%' change string. Returns None if past is unavailable."""
    if past is None or past == 0:
        return None
    pct = (latest - past) / past * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}%"


def compute_fields(iid, history):
    """
    Compute the full set of fields to write for one instrument.
    Returns a dict, or None if history is empty.
    """
    if not history:
        return None

    latest      = history[-1]
    latest_date = latest["date"]
    latest_close = latest["close"]

    latest_dt = datetime.strptime(latest_date, "%Y-%m-%d").date()

    # Lookback reference dates
    d_1w = str(latest_dt - timedelta(days=7))
    d_1m = str(latest_dt - timedelta(days=30))
    d_3m = str(latest_dt - timedelta(days=91))

    c_1w = find_close_on_or_before(history, d_1w)
    c_1m = find_close_on_or_before(history, d_1m)
    c_3m = find_close_on_or_before(history, d_3m)

    return {
        "price":       str(round(latest_close, 2)),
        "change_1w":   fmt_change(latest_close, c_1w),
        "change_1m":   fmt_change(latest_close, c_1m),
        "change_3m":   fmt_change(latest_close, c_3m),
        "spark":       history,   # full history, always rebuilt from source
        "last_updated": latest_date,
    }


# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------

def sync(apply=False):
    today = date.today()
    print(f"CB_sync_sheet.py — {'APPLY' if apply else 'PREVIEW'} mode")
    print(f"Date:  {today}")
    print(f"Sheet: {SHEET_ID}")
    print()

    # --- Connect ---
    print("Connecting to Google Sheets...")
    try:
        sheet = connect_sheet()
    except Exception as exc:
        print(f"[FATAL] Could not connect to Google Sheets: {exc}")
        sys.exit(1)

    # --- Read both tabs ---
    print("Reading price history tabs...")
    auto_rows   = read_tab(sheet, AUTO_TAB_NAME)
    manual_rows = read_tab(sheet, MANUAL_TAB_NAME)
    print()

    total_rows = len(auto_rows) + len(manual_rows)
    if total_rows == 0:
        print("[FATAL] No rows found in either tab. Nothing to sync.")
        sys.exit(1)

    # --- Merge ---
    history = build_history(auto_rows, manual_rows)

    print("Instruments with history:")
    for iid, rows in sorted(history.items()):
        print(f"  {iid}: {len(rows)} days  ({rows[0]['date']} to {rows[-1]['date']})")
    print()

    # --- Load CB_data.json ---
    if not DATA_JSON_PATH.exists():
        print(f"[FATAL] CB_data.json not found at {DATA_JSON_PATH}")
        sys.exit(1)

    with open(DATA_JSON_PATH) as f:
        data = json.load(f)

    # --- Compute updates ---
    updates       = {}   # instrument_id -> fields dict
    vag_warnings  = []   # instruments that will need story updates
    no_data_warns = []   # instruments with no history rows

    for instrument in data["instruments"]:
        iid  = instrument["id"]
        hist = history.get(iid)

        if not hist:
            no_data_warns.append(iid)
            continue

        fields = compute_fields(iid, hist)
        if not fields:
            no_data_warns.append(iid)
            continue

        updates[iid] = fields

        # value_at_generation mismatch check.
        # We warn here, but do NOT update value_at_generation — that field
        # is owned by CB_update_stories.py. The build will fail if stories
        # are not refreshed before running CB_build.py.
        old_price = str(instrument.get("price", "")).strip()
        new_price = fields["price"]
        vag       = str(instrument.get("value_at_generation", "")).strip()

        if new_price != old_price and vag == old_price:
            vag_warnings.append(
                f"  [VAG WARNING] {iid}: price {old_price} -> {new_price}. "
                f"value_at_generation ({vag}) will mismatch. "
                f"Run CB_update_stories.py before CB_build.py."
            )
        elif new_price != old_price and vag != old_price:
            # vag already mismatched before this run — still needs stories
            vag_warnings.append(
                f"  [VAG WARNING] {iid}: price changing to {new_price}. "
                f"value_at_generation is '{vag}' — stories already stale. "
                f"Run CB_update_stories.py before CB_build.py."
            )

    # --- Print preview ---
    print("Proposed updates:")
    for iid, fields in sorted(updates.items()):
        old_instr = next((i for i in data["instruments"] if i["id"] == iid), {})
        old_price = old_instr.get("price", "?")
        old_spark = len(old_instr.get("spark", []))
        new_spark = len(fields["spark"])
        print(f"  {iid}:")
        print(f"    price:      {old_price} -> {fields['price']}")
        print(f"    change_1w:  {fields['change_1w']}")
        print(f"    change_1m:  {fields['change_1m']}")
        print(f"    change_3m:  {fields['change_3m']}")
        print(f"    spark:      {old_spark} pts -> {new_spark} pts "
              f"({fields['spark'][0]['date']} to {fields['spark'][-1]['date']})")
        print(f"    last_updated: {fields['last_updated']}")
    print()

    if no_data_warns:
        print(f"No history found for (spark will remain empty):")
        for iid in no_data_warns:
            print(f"  {iid}")
        print()

    if vag_warnings:
        print("value_at_generation warnings:")
        for w in vag_warnings:
            print(w)
        print()
        print("  Action required: run CB_update_stories.py --apply after this sync,")
        print("  then CB_build.py. The build will fail if value_at_generation")
        print("  mismatches exist.")
        print()

    if not apply:
        print("Preview only. Run with --apply to write to CB_data.json.")
        return

    # --- Apply updates ---
    for instrument in data["instruments"]:
        iid = instrument["id"]
        if iid not in updates:
            continue

        fields = updates[iid]
        instrument["price"]        = fields["price"]
        instrument["last_updated"] = fields["last_updated"]
        instrument["spark"]        = fields["spark"]

        # Only overwrite change fields if we successfully computed them
        # (i.e. sufficient history exists for the lookback period)
        if fields["change_1w"] is not None:
            instrument["change_1w"] = fields["change_1w"]
        if fields["change_1m"] is not None:
            instrument["change_1m"] = fields["change_1m"]
        if fields["change_3m"] is not None:
            instrument["change_3m"] = fields["change_3m"]

    # Write
    with open(DATA_JSON_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Written to {DATA_JSON_PATH}")
    print(f"  {len(updates)} instruments updated")
    if no_data_warns:
        print(f"  {len(no_data_warns)} instruments unchanged (no history): {no_data_warns}")
    print()
    print("Done.")
    print()

    if vag_warnings:
        print("IMPORTANT: value_at_generation mismatches exist.")
        print("CB_build.py will abort until CB_update_stories.py is run.")
        # Exit with non-zero so callers and CI pipelines can detect this state
        sys.exit(2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync price history from Google Sheets into CB_data.json."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write to CB_data.json (default is preview mode, no writes).",
    )
    args = parser.parse_args()
    sync(apply=args.apply)
