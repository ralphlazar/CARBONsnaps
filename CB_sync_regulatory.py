"""
sync_regulatory.py

Sync layer script. Reads the REGULATORY-TRACKER Google Sheet (Events tab),
validates all rows, and writes to data.json.

Pipeline architecture rule: this script never contacts any external API.
It reads exclusively from Google Sheets via gspread and writes to data.json.

Usage:
    python3 sync_regulatory.py              # preview mode — prints what would change, no writes
    python3 sync_regulatory.py --apply      # writes to data.json

Auth: requires service account key at path set by REGULATORY_KEY env var,
or falls back to regulatory-key.json in the script directory.

Sheet ID: set via REGULATORY_SHEET_ID env var, or hardcode below.
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

SHEET_ID = os.environ.get("REGULATORY_SHEET_ID", "1Tvg30ZkRbomed3zVIx42DLcAAYVK9q50m4yX-hJwu68")
TAB_NAME = "Events"
DATA_JSON_PATH = Path(__file__).parent / "CB_data.json"
KEY_PATH = os.environ.get("REGULATORY_KEY", Path(__file__).parent / "CB_market-stats-key.json")

# How many days before a reviewed date triggers a stale warning
STALE_DAYS = 30

# Controlled vocabularies — sync script validates against these
VALID_JURISDICTIONS = {
    "EU", "California", "UK", "US-Federal", "ICAO",
    "UN-Article6", "Global", "Australia", "Canada", "China", "Other"
}

VALID_INSTRUMENTS = {
    "EUA", "CCA", "UKA", "CORSIA",
    "LCFS", "RIN", "45Z", "VCM"
}

VALID_EVENT_TYPES = {
    "Consultation", "Proposal", "Vote", "Implementation",
    "Review", "Election", "Registry-Update", "Court-Decision", "Guidance",
    "Cap Change", "Rule Change", "Regulation", "Negotiation",
    "Phase Change", "Price Floor"
}

VALID_STATUSES = {"Upcoming", "Active", "Decided", "Delayed", "Withdrawn"}

VALID_DIRECTIONS = {"Bullish", "Bearish", "Neutral", "Mixed"}

VALID_CONFIDENCE = {"High", "Medium", "Low"}

VALID_MAGNITUDE = {"High", "Medium", "Low"}

# Expected column headers in order (must match sheet exactly)
EXPECTED_HEADERS = [
    "event_id", "title", "jurisdiction", "instruments_affected",
    "event_type", "status", "next_date", "direction",
    "confidence", "magnitude", "summary", "date_last_reviewed", "display",
    "analyst_note", "source_label", "source_url"
]

# ---------------------------------------------------------------------------
# Sheet connection
# ---------------------------------------------------------------------------

def connect_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    creds = Credentials.from_service_account_file(str(KEY_PATH), scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    return sheet.worksheet(TAB_NAME)


def fetch_rows(ws):
    """Return list of dicts keyed by header name. Skips blank rows."""
    all_values = ws.get_all_values()
    if not all_values:
        raise ValueError("Sheet is empty.")

    headers = all_values[0]

    # Validate headers
    missing = [h for h in EXPECTED_HEADERS if h not in headers]
    extra = [h for h in headers if h not in EXPECTED_HEADERS]
    if missing:
        raise ValueError(f"Sheet is missing expected columns: {missing}")
    if extra:
        print(f"  [WARN] Sheet has unexpected columns (ignored): {extra}")

    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        # Pad short rows
        while len(row) < len(headers):
            row.append("")
        record = {headers[j]: row[j].strip() for j in range(len(headers))}
        # Skip entirely blank rows
        if not any(record.values()):
            continue
        record["_row_number"] = i
        rows.append(record)

    return rows


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def parse_date(val, field, event_id, warnings):
    """Parse date string. Accepts YYYY-MM-DD or DD/MM/YYYY. Returns date or None."""
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    # Not a parseable date — could be a free-text quarter/half-year string, skip silently
    return None


def validate_row(row, warnings, errors):
    """
    Validate a single row against controlled vocabularies and required fields.
    Appends to warnings (non-fatal) or errors (fatal — row will be excluded).
    Returns cleaned dict ready for data.json, or None if fatal errors found.
    """
    eid = row.get("event_id", "UNKNOWN")
    row_errors = []

    # Required fields
    for required in ["event_id", "title", "jurisdiction", "instruments_affected",
                     "event_type", "status", "direction", "summary"]:
        if not row.get(required):
            row_errors.append(f"  [ERROR] Row {row['_row_number']} ({eid}): missing required field '{required}'")

    # Controlled vocab checks
    if row.get("jurisdiction") and row["jurisdiction"] not in VALID_JURISDICTIONS:
        row_errors.append(f"  [ERROR] {eid}: unknown jurisdiction '{row['jurisdiction']}'")

    if row.get("event_type") and row["event_type"] not in VALID_EVENT_TYPES:
        row_errors.append(f"  [ERROR] {eid}: unknown event_type '{row['event_type']}'")

    if row.get("status") and row["status"] not in VALID_STATUSES:
        row_errors.append(f"  [ERROR] {eid}: unknown status '{row['status']}'")

    if row.get("direction") and row["direction"] not in VALID_DIRECTIONS:
        row_errors.append(f"  [ERROR] {eid}: unknown direction '{row['direction']}'")

    if row.get("confidence") and row["confidence"] not in VALID_CONFIDENCE:
        row_errors.append(f"  [ERROR] {eid}: unknown confidence '{row['confidence']}'")

    if row.get("magnitude") and row["magnitude"] not in VALID_MAGNITUDE:
        row_errors.append(f"  [ERROR] {eid}: unknown magnitude '{row['magnitude']}'")

    # Instruments — validate each token
    raw_instruments = row.get("instruments_affected", "")
    instruments = [i.strip() for i in raw_instruments.split(",") if i.strip()]
    unknown_instruments = [i for i in instruments if i not in VALID_INSTRUMENTS]
    if unknown_instruments:
        row_errors.append(f"  [ERROR] {eid}: unknown instruments {unknown_instruments}")

    # display flag
    display_raw = row.get("display", "").upper()
    if display_raw not in ("TRUE", "FALSE"):
        row_errors.append(f"  [ERROR] {eid}: display must be TRUE or FALSE, got '{row.get('display')}'")

    if row_errors:
        errors.extend(row_errors)
        return None

    # Date parsing (warnings only, not errors — missing dates are allowed)
    today = date.today()
    next_date = parse_date(row.get("next_date"), "next_date", eid, warnings)
    date_last_reviewed = parse_date(row.get("date_last_reviewed"), "date_last_reviewed", eid, warnings)

    # Stale check: active/upcoming rows not reviewed in STALE_DAYS
    is_active = row["status"] in ("Active", "Upcoming")
    is_stale = False
    if is_active and date_last_reviewed:
        days_since = (today - date_last_reviewed).days
        if days_since > STALE_DAYS:
            warnings.append(
                f"  [STALE] {eid}: last reviewed {days_since} days ago ({date_last_reviewed}). "
                f"Active/Upcoming rows must be reviewed within {STALE_DAYS} days."
            )
            is_stale = True
    elif is_active and not date_last_reviewed:
        warnings.append(f"  [WARN] {eid}: active row has no date_last_reviewed.")

    # Build clean record
    return {
        "event_id": row["event_id"],
        "title": row["title"],
        "jurisdiction": row["jurisdiction"],
        "instruments_affected": instruments,
        "event_type": row["event_type"],
        "status": row["status"],
        "next_date": row.get("next_date") or None,
        "direction": row["direction"],
        "confidence": row.get("confidence") or None,
        "magnitude": row.get("magnitude") or None,
        "summary": row["summary"],
        "analyst_note": row.get("analyst_note") or None,
        "source_label": row.get("source_label") or None,
        "source_url": row.get("source_url") or None,
        "date_last_reviewed": str(date_last_reviewed) if date_last_reviewed else None,
        "is_stale": is_stale,
    }


# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------

def sync(apply=False):
    today = date.today()
    warnings = []
    errors = []

    print(f"sync_regulatory.py — {'APPLY' if apply else 'PREVIEW'} mode")
    print(f"Date: {today}")
    print(f"Sheet ID: {SHEET_ID}")
    print()

    # --- Fetch from sheet ---
    print("Connecting to Google Sheets...")
    try:
        ws = connect_sheet()
    except Exception as e:
        print(f"[FATAL] Could not connect to sheet: {e}")
        sys.exit(1)

    print(f"Fetching rows from tab '{TAB_NAME}'...")
    rows = fetch_rows(ws)
    print(f"  {len(rows)} non-blank rows found.")
    print()

    # --- Validate and build event list ---
    all_events = []
    display_events = []
    stale_ids = []

    for row in rows:
        cleaned = validate_row(row, warnings, errors)
        if cleaned is None:
            continue

        all_events.append(cleaned)

        if row.get("display", "").upper() == "TRUE":
            display_events.append(cleaned)

        if cleaned["is_stale"]:
            stale_ids.append(cleaned["event_id"])

    # --- Print validation report ---
    if errors:
        print(f"ERRORS ({len(errors)} — these rows will be excluded):")
        for e in errors:
            print(e)
        print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(w)
        print()

    # --- Summary ---
    print(f"Results:")
    print(f"  Total rows read:       {len(rows)}")
    print(f"  Valid rows:            {len(all_events)}")
    print(f"  Display=TRUE (public): {len(display_events)}")
    print(f"  Stale warnings:        {len(stale_ids)}")
    print(f"  Rows with errors:      {len(rows) - len(all_events)}")
    print()

    # Sort display events by next_date (nulls last)
    display_events.sort(
        key=lambda e: (e["next_date"] is None, e["next_date"] or "")
    )

    # --- Load data.json ---
    if not DATA_JSON_PATH.exists():
        print(f"[FATAL] CB_data.json not found at {DATA_JSON_PATH}")
        sys.exit(1)

    with open(DATA_JSON_PATH) as f:
        data = json.load(f)

    # --- Carry forward existing scenarios from data.json ---
    # The sync script replaces the events array wholesale, which would discard
    # scenarios already generated by CB_update_scenarios.py. Preserve them by
    # copying scenario-related fields from the old event wherever event_id matches.
    SCENARIO_FIELDS = (
        "scenarios",
        "scenarios_at_generation",
        "scenarios_content_snapshot",
    )
    old_events_by_id = {
        ev["event_id"]: ev
        for ev in data.get("regulatory", {}).get("events", [])
    }
    preserved = 0
    for ev in display_events:
        old_ev = old_events_by_id.get(ev["event_id"])
        if old_ev:
            for field in SCENARIO_FIELDS:
                if field in old_ev:
                    ev[field] = old_ev[field]
            if old_ev.get("scenarios"):
                preserved += 1

    # --- Build regulatory block ---
    regulatory_block = {
        "events": display_events,
        "last_synced": str(today),
        "stale_warnings": stale_ids,
        "total_events": len(display_events),
    }

    # --- Preview diff ---
    old_block = data.get("regulatory", {})
    old_count = len(old_block.get("events", []))
    new_count = len(display_events)

    print(f"Diff:")
    print(f"  Events in data.json now:   {old_count}")
    print(f"  Events after sync:         {new_count}")
    print(f"  Scenarios preserved:       {preserved}")
    print(f"  Scenarios to generate:     {new_count - preserved}")
    print(f"  Last synced (current):     {old_block.get('last_synced', 'never')}")
    print(f"  Last synced (after):       {today}")
    if stale_ids:
        print(f"  Stale event IDs:           {stale_ids}")
    print()

    if not apply:
        print("Preview only. Run with --apply to write to data.json.")
        if errors:
            print(f"[NOTE] {len(errors)} rows had errors and would be excluded.")
        return

    # --- Write ---
    if errors:
        print(f"[WARN] Writing with {len(errors)} excluded rows. Fix errors and re-run to include them.")

    data["regulatory"] = regulatory_block
    with open(DATA_JSON_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Written to {DATA_JSON_PATH}")
    print(f"  data.regulatory.events: {new_count} events")
    print(f"  data.regulatory.last_synced: {today}")
    if stale_ids:
        print(f"  data.regulatory.stale_warnings: {stale_ids}")
    print()
    print("Done.")

    # Exit with error code if stale warnings exist — audit_ritual.py can check this
    if stale_ids:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync regulatory tracker sheet to data.json")
    parser.add_argument("--apply", action="store_true", help="Write to data.json (default is preview)")
    args = parser.parse_args()
    sync(apply=args.apply)
