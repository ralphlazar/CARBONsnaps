"""
CB_populate_regulatory_sources.py

One-time helper script. Writes source_label and source_url values
to cols O and P of the REGULATORY-TRACKER Events tab for all 15 events.

This is a data-entry assist, not part of the daily pipeline.
Run once after verifying sources. Safe to re-run — overwrites O/P only.

Usage:
    python3 CB_populate_regulatory_sources.py              # preview (print only)
    python3 CB_populate_regulatory_sources.py --apply      # write to sheet
"""

import os
import sys
import argparse
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = os.environ.get("REGULATORY_SHEET_ID", "1Tvg30ZkRbomed3zVIx42DLcAAYVK9q50m4yX-hJwu68")
TAB_NAME = "Events"
KEY_PATH = os.environ.get("REGULATORY_KEY", Path(__file__).parent / "CB_market-stats-key.json")

# Source citations keyed by event_id
SOURCES = {
    "REG-001": {
        "source_label": "European Parliament & Council, Directive (EU) 2023/959, 10 May 2023",
        "source_url":   "https://eur-lex.europa.eu/eli/dir/2023/959/oj/eng",
    },
    "REG-002": {
        "source_label": "European Parliament & Council, Decision (EU) 2023/852 amending Decision 2015/1814 (MSR), 19 April 2023",
        "source_url":   "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023D0852",
    },
    "REG-003": {
        "source_label": "European Parliament & Council, Regulation (EU) 2023/956 establishing CBAM, 10 May 2023",
        "source_url":   "https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32023R0956",
    },
    "REG-004": {
        "source_label": "European Parliament & Council, Directive (EU) 2023/959, Chapter IVa (ETS2), 10 May 2023",
        "source_url":   "https://eur-lex.europa.eu/eli/dir/2023/959/oj/eng",
    },
    "REG-005": {
        "source_label": "UK-EU Summit, Common Understanding on a Renewed Agenda for Cooperation (ETS linkage, Chapter IV), 19 May 2025",
        "source_url":   "https://www.gov.uk/government/publications/uk-eu-summit-may-2025-common-understanding",
    },
    "REG-006": {
        "source_label": "UK ETS Authority (DESNZ), UK ETS Policy Overview; Net Zero Cap effective January 2024",
        "source_url":   "https://www.gov.uk/government/publications/uk-emissions-trading-scheme-uk-ets-policy-overview/uk-emissions-trading-scheme-uk-ets-a-policy-overview",
    },
    "REG-007": {
        "source_label": "CARB, Cap-and-Invest Program Proposed Rulemaking (AB 1207/SB 840), public comment Jan-Mar 2026",
        "source_url":   "https://ww2.arb.ca.gov/our-work/programs/cap-and-invest-program",
    },
    "REG-008": {
        "source_label": "CARB, Low Carbon Fuel Standard Regulation Amendment, Board approved 8 November 2024; OAL effective July 2025",
        "source_url":   "https://ww2.arb.ca.gov/our-work/programs/low-carbon-fuel-standard/about",
    },
    "REG-009": {
        "source_label": "ICAO, Annex 16 Volume IV (CORSIA SARPs) 2nd Edition, effective 1 January 2024; Assembly Resolution A41-22, October 2022",
        "source_url":   "https://www.icao.int/CORSIA/sarps-annex-16-volume-iv",
    },
    "REG-010": {
        "source_label": "ICAO Council, CORSIA Eligible Emissions Units Document (updated October 2025); TAB 2024 assessment cycle",
        "source_url":   "https://www.icao.int/environmental-protection/CORSIA/Pages/default.aspx",
    },
    "REG-011": {
        "source_label": "US EPA, Proposed Rule: RFS Standards for 2026 and 2027, 90 Fed. Reg. 25786, 17 June 2025",
        "source_url":   "https://www.federalregister.gov/documents/2025/06/17/2025-11128/renewable-fuel-standard-rfs-program-standards-for-2026-and-2027-partial-waiver-of-2025-cellulosic",
    },
    "REG-012": {
        "source_label": "IRS/Treasury, Notice 2025-10 and Notice 2025-11, Section 45Z Clean Fuel Production Credit Guidance, 10 January 2025",
        "source_url":   "https://www.irs.gov/credits-deductions/clean-fuel-production-credit",
    },
    "REG-013": {
        "source_label": "UNFCCC Article 6.4 Supervisory Body; COP29 Decision on Article 6.4 Mechanism Standards, November 2024",
        "source_url":   "https://unfccc.int/process-and-meetings/bodies/constituted-bodies/article-64-supervisory-body",
    },
    "REG-014": {
        "source_label": "Verra, VM0048 Reducing Emissions from Deforestation and Forest Degradation (VCS Program), launched 27 November 2023",
        "source_url":   "https://verra.org/methodologies/vm0007-redd-methodology-framework-redd-mf-v1-8/",
    },
    "REG-015": {
        "source_label": "CARB, 2026 Annual Auction Reserve Price Notice (Cap-and-Trade Regulation, Appendix C), December 2025",
        "source_url":   "https://ww2.arb.ca.gov/our-work/programs/cap-and-trade-program/auction-information",
    },
}


def main(apply=False):
    print(f"CB_populate_regulatory_sources.py — {'APPLY' if apply else 'PREVIEW'} mode")
    print()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(str(KEY_PATH), scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    ws = sheet.worksheet(TAB_NAME)

    all_values = ws.get_all_values()
    headers = all_values[0]

    try:
        event_id_col = headers.index("event_id")
        source_label_col = headers.index("source_label")
        source_url_col = headers.index("source_url")
    except ValueError as e:
        print(f"[FATAL] Column not found: {e}")
        print("Make sure source_label (col O) and source_url (col P) headers exist in the sheet.")
        sys.exit(1)

    updates = []
    for i, row in enumerate(all_values[1:], start=2):
        eid = row[event_id_col].strip() if len(row) > event_id_col else ""
        if eid in SOURCES:
            src = SOURCES[eid]
            updates.append({
                "row": i,
                "event_id": eid,
                "source_label": src["source_label"],
                "source_url": src["source_url"],
                "source_label_col": source_label_col + 1,  # gspread is 1-indexed
                "source_url_col": source_url_col + 1,
            })

    print(f"Events to update: {len(updates)}")
    for u in updates:
        print(f"  Row {u['row']:2d}  {u['event_id']:10s}  {u['source_label'][:60]}...")
    print()

    if not apply:
        print("Preview only. Run with --apply to write to sheet.")
        return

    # Batch update
    cell_updates = []
    for u in updates:
        cell_updates.append(gspread.Cell(u["row"], u["source_label_col"], u["source_label"]))
        cell_updates.append(gspread.Cell(u["row"], u["source_url_col"], u["source_url"]))

    ws.update_cells(cell_updates, value_input_option="RAW")
    print(f"Written {len(updates)} rows ({len(cell_updates)} cells) to sheet.")
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    main(apply=args.apply)
