"""
CB_add_new_events.py

One-off script: appends REG-016 to REG-022 to the Events tab of the
CARBONsnaps regulatory tracker Google Sheet.

Run from the CARBONsnaps project directory:
    python3 CB_add_new_events.py            # preview — prints rows, no writes
    python3 CB_add_new_events.py --apply    # appends rows to sheet
"""

import os
import sys
import argparse
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1Tvg30ZkRbomed3zVIx42DLcAAYVK9q50m4yX-hJwu68"
TAB_NAME = "Events"
KEY_PATH = Path(__file__).parent / "CB_market-stats-key.json"

# ---------------------------------------------------------------------------
# New event rows — values must align with sheet column order exactly.
# Columns (17 total, matching updated EXPECTED_HEADERS in CB_sync_regulatory.py):
#   event_id, title, jurisdiction, instruments_affected, event_type,
#   status, next_date, direction, confidence, magnitude, summary,
#   date_last_reviewed, display, analyst_note, source_label, source_url,
#   note_version
# ---------------------------------------------------------------------------

NEW_EVENTS = [
    {
        "event_id": "REG-016",
        "title": "EU ETS maritime 100% compliance phase-in",
        "jurisdiction": "EU",
        "instruments_affected": "EUA",
        "event_type": "Phase Change",
        "status": "Active",
        "next_date": "01/01/2026",
        "direction": "Bullish",
        "confidence": "High",
        "magnitude": "Medium",
        "summary": "From 1 January 2026 shipping companies must surrender EUAs for 100% of verified CO2, up from 70% in 2025. The phase-in is complete. New demand from ~5,000 GT vessels now fully priced into the cap.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "Effective demand increase of ~30% on the maritime surrender tranche vs 2025. Watch verified emissions data vs allowances surrendered — any shortfall triggers cancellation from the auction calendar.",
        "source_label": "European Commission Climate Action",
        "source_url": "https://climate.ec.europa.eu",
        "note_version": "",
    },
    {
        "event_id": "REG-017",
        "title": "UK ETS Auction Reserve Price increase £22→£28",
        "jurisdiction": "UK",
        "instruments_affected": "UKA",
        "event_type": "Price Floor",
        "status": "Active",
        "next_date": "08/04/2026",
        "direction": "Bullish",
        "confidence": "High",
        "magnitude": "Medium",
        "summary": "The UK ETS Auction Reserve Price rises from £22 to £28, taking effect for the 8 April 2026 auction, an increase of 27%. Mandated by the Greenhouse Gas Emissions Trading Scheme Auctioning (Amendment) Regulations 2026.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "A hard price floor rise of this magnitude is a direct bullish signal for UKA. From 2027 the ARP increases annually in line with GDP Deflator, locking in real-terms escalation.",
        "source_label": "UK ETS Authority / GOV.UK",
        "source_url": "https://www.gov.uk/government/publications/uk-emissions-trading-scheme-uk-ets-policy-overview/uk-emissions-trading-scheme-uk-ets-a-policy-overview",
        "note_version": "",
    },
    {
        "event_id": "REG-018",
        "title": "UK ETS maritime expansion launch",
        "jurisdiction": "UK",
        "instruments_affected": "UKA",
        "event_type": "Phase Change",
        "status": "Upcoming",
        "next_date": "01/07/2026",
        "direction": "Bullish",
        "confidence": "High",
        "magnitude": "Medium",
        "summary": "The UK government has confirmed 1 July 2026 as the launch date for the UK ETS maritime regime, covering domestic shipping journeys for vessels of 5,000 GT or above. A double-surrender arrangement applies for 2026-2027, with allowances due by 30 April 2028.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "New demand entrants from mid-2026. Double-surrender in year one means the financial impact is deferred but certain — watch onboarding volumes for Q3 UKA auction demand signal.",
        "source_label": "UK ETS Authority / GOV.UK",
        "source_url": "https://www.gov.uk/government/publications/uk-emissions-trading-scheme-uk-ets-policy-overview/uk-emissions-trading-scheme-uk-ets-a-policy-overview",
        "note_version": "",
    },
    {
        "event_id": "REG-019",
        "title": "EU ETS post-2030 Commission revision proposal",
        "jurisdiction": "EU",
        "instruments_affected": "EUA",
        "event_type": "Proposal",
        "status": "Upcoming",
        "next_date": "2026-Q3",
        "direction": "Mixed",
        "confidence": "Medium",
        "magnitude": "High",
        "summary": "The 2026 Commission work programme includes a climate package with a proposal to update the EU ETS expected by July 2026. The review covers carbon removals, new sector inclusions, carbon leakage post-CBAM phase-out, and possible linking with other carbon markets.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "Biggest structural uncertainty for EUA pricing beyond 2030. Scope of carbon removals inclusion and whether aviation free allocation phase-out timeline is hardened are the key variables to watch.",
        "source_label": "European Parliament Think Tank / EPRS",
        "source_url": "https://www.europarl.europa.eu/thinktank/en/document/EPRS_BRI(2026)782615",
        "note_version": "",
    },
    {
        "event_id": "REG-020",
        "title": "EU ETS post-2030 public consultation close",
        "jurisdiction": "EU",
        "instruments_affected": "EUA",
        "event_type": "Consultation",
        "status": "Active",
        "next_date": "04/05/2026",
        "direction": "Neutral",
        "confidence": "High",
        "magnitude": "Low",
        "summary": "The European Commission's public consultation on the post-2030 EU ETS implementation package runs from 9 February to 4 May 2026. It explores how ETS-covered emissions interact with national climate targets in the post-2030 framework.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "Consultation close on 4 May is a soft catalyst — direction of stakeholder submissions informs the July proposal above. Watch for industry positions on scope expansion and removal crediting.",
        "source_label": "European Commission / carbongap.org tracker",
        "source_url": "https://tracker.carbongap.org/policy/eu-emissions-trading-system/",
        "note_version": "",
    },
    {
        "event_id": "REG-021",
        "title": "EU ETS annual surrender deadline (2025 emissions)",
        "jurisdiction": "EU",
        "instruments_affected": "EUA",
        "event_type": "Regulation",
        "status": "Upcoming",
        "next_date": "30/04/2026",
        "direction": "Bullish",
        "confidence": "High",
        "magnitude": "Medium",
        "summary": "30 April 2026 is the annual deadline for EU ETS installations and aircraft operators to surrender allowances covering their 2025 verified emissions. A recurring compliance demand event that drives EUA buying pressure through Q1 each year.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "Near-term bullish price dynamic. Any shortfall vs verified emissions amplifies spot buying. Monitor EU registry data on verified emissions vs outstanding positions into April.",
        "source_label": "European Commission Climate Action",
        "source_url": "https://climate.ec.europa.eu",
        "note_version": "",
    },
    {
        "event_id": "REG-022",
        "title": "UK Carbon Border Adjustment Mechanism launch",
        "jurisdiction": "UK",
        "instruments_affected": "UKA",
        "event_type": "Implementation",
        "status": "Upcoming",
        "next_date": "01/01/2027",
        "direction": "Bullish",
        "confidence": "High",
        "magnitude": "Medium",
        "summary": "The UK government confirmed a Carbon Border Adjustment Mechanism launching 1 January 2027, with enabling legislation in the Finance Bill 2025-26. Indirect emissions will not be included until 2029 at earliest.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "Structural demand anchor for UKA pricing as CBAM aligns import carbon costs with the domestic ETS price. Creates medium-term ceiling on free allocation phase-down speed and supports UKA floor.",
        "source_label": "UK Government Finance Bill 2025-26 / HMRC",
        "source_url": "https://www.gov.uk",
        "note_version": "",
    },
]


def connect_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file(str(KEY_PATH), scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    return sheet.worksheet(TAB_NAME)


def run(apply=False):
    print(f"CB_add_new_events.py — {'APPLY' if apply else 'PREVIEW'} mode")
    print()

    # Connect and read current headers
    print("Connecting to Google Sheets...")
    ws = connect_sheet()
    headers = ws.row_values(1)
    print(f"  Headers ({len(headers)}): {headers}")

    current_ids = [
        row[0] for row in ws.get_all_values()[1:] if row and row[0].strip()
    ]
    print(f"  Existing event IDs: {current_ids}")
    print()

    # Build rows in header order, skip any already present
    rows_to_append = []
    for ev in NEW_EVENTS:
        if ev["event_id"] in current_ids:
            print(f"  SKIP {ev['event_id']} — already in sheet")
            continue
        row = [ev.get(h, "") for h in headers]
        rows_to_append.append((ev["event_id"], ev["title"], row))

    if not rows_to_append:
        print("Nothing to add — all 7 events already present.")
        return

    print(f"{'Appending' if apply else 'Would append'} {len(rows_to_append)} rows:")
    for eid, title, row in rows_to_append:
        print(f"  {'✓' if apply else '○'} {eid}  {title}")

    if not apply:
        print()
        print("Preview only. Run with --apply to write to the sheet.")
        return

    print()
    for eid, title, row in rows_to_append:
        ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"  Appended {eid}")

    print()
    print(f"Done. {len(rows_to_append)} rows added to '{TAB_NAME}' tab.")
    print()
    print("Next steps:")
    print("  python3 CB_sync_regulatory.py --apply")
    print("  python3 CB_update_scenarios.py --apply --stale-only")
    print("  python3 CB_build.py && open index.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Append REG-016 to REG-022 to the Events sheet")
    parser.add_argument("--apply", action="store_true", help="Write to sheet (default is preview)")
    args = parser.parse_args()
    run(apply=args.apply)
