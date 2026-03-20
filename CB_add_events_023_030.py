"""
CB_add_events_023_030.py

One-off script: appends REG-023 to REG-030 to the Events tab of the
CARBONsnaps regulatory tracker Google Sheet.

Run from the CARBONsnaps project directory:
    python3 CB_add_events_023_030.py            # preview — prints rows, no writes
    python3 CB_add_events_023_030.py --apply    # appends rows to sheet
"""

import argparse
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1Tvg30ZkRbomed3zVIx42DLcAAYVK9q50m4yX-hJwu68"
TAB_NAME = "Events"
KEY_PATH = Path(__file__).parent / "CB_market-stats-key.json"

# ---------------------------------------------------------------------------
# New event rows
# Column order (17 cols, matching sheet):
#   event_id, title, jurisdiction, instruments_affected, event_type,
#   status, next_date, direction, confidence, magnitude, summary,
#   date_last_reviewed, display, analyst_note, source_label, source_url,
#   note_version
# ---------------------------------------------------------------------------

NEW_EVENTS = [
    {
        "event_id": "REG-023",
        "title": "EU-UK ETS formal linking negotiations",
        "jurisdiction": "UK",
        "instruments_affected": "UKA, EUA",
        "event_type": "Negotiation",
        "status": "Active",
        "next_date": "2026-Q4",
        "direction": "Bullish",
        "confidence": "Medium",
        "magnitude": "High",
        "summary": "Formal EU-UK ETS linking negotiations launched the week of 19 January 2026. EU Climate Commissioner Wopke Hoekstra confirmed both sides are aiming to conclude as soon as possible, with no specific timeline set. The EU Council unanimously backed the negotiating mandate in November 2025; the Commission is now authorised to negotiate. This row tracks the active negotiations phase; milestone rows (technical design, agreement in principle, ratification) will be added as dates are confirmed.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "The single most structurally important medium-term event for UKA pricing. Convergence with EUA price is the implied outcome of a successful link — UKA currently trades at a material discount. Watch for technical design milestones and any public signals on timeline from either side.",
        "source_label": "ICAP / ClearBlue Markets",
        "source_url": "https://icapcarbonaction.com",
        "note_version": "",
    },
    {
        "event_id": "REG-024",
        "title": "EU ETS aviation stop-the-clock expiry and CORSIA assessment",
        "jurisdiction": "EU",
        "instruments_affected": "EUA, CORSIA",
        "event_type": "Review",
        "status": "Upcoming",
        "next_date": "2026-H2",
        "direction": "Mixed",
        "confidence": "Medium",
        "magnitude": "Medium",
        "summary": "The stop-the-clock mechanism limiting EU ETS aviation scope to intra-EU flights expires at end of 2026. The European Commission is scheduled to publish a CORSIA assessment by mid-2026 to determine whether it is sufficiently aligned with the Paris Agreement. Subject to the outcome, a legislative proposal could extend EU ETS scope to departing extra-European flights.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "Outcome is binary and high-impact: a negative CORSIA assessment could trigger EU ETS extension to extra-European departures, materially increasing aviation demand for EUAs. A positive assessment preserves the status quo. Commission report timing (mid-2026) is the near-term catalyst to watch.",
        "source_label": "Normec Verifavia / White & Case / ICAP",
        "source_url": "https://icapcarbonaction.com",
        "note_version": "",
    },
    {
        "event_id": "REG-025",
        "title": "EU ETS Commission statutory review (July 2026)",
        "jurisdiction": "EU",
        "instruments_affected": "EUA",
        "event_type": "Review",
        "status": "Upcoming",
        "next_date": "31/07/2026",
        "direction": "Mixed",
        "confidence": "High",
        "magnitude": "Medium",
        "summary": "Distinct from the post-2030 proposal (REG-019). The Commission has a statutory obligation to report by end of July 2026 on: negative emissions accounting under EU ETS, feasibility of lowering the 20MW installation threshold, municipal waste incineration inclusion, CCU double-counting, and the functioning of aviation ETS and CORSIA.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "Hard statutory deadline creates a defined catalyst. Waste incineration inclusion and negative emissions accounting are the variables with the most direct price read-across. CCU double-counting clarification could affect industrial sector compliance costs. Low probability of major structural surprise but watch for scope signals on waste and negative emissions.",
        "source_label": "ICAP ETS factsheet",
        "source_url": "https://icapcarbonaction.com",
        "note_version": "",
    },
    {
        "event_id": "REG-026",
        "title": "EU ETS free allocation CBAM phase-out begins",
        "jurisdiction": "EU",
        "instruments_affected": "EUA",
        "event_type": "Phase Change",
        "status": "Active",
        "next_date": "01/01/2026",
        "direction": "Bullish",
        "confidence": "High",
        "magnitude": "Medium",
        "summary": "From 2026, free allocation to CBAM-covered sectors (iron and steel, cement, aluminium, fertilisers, hydrogen) begins a gradual phase-out. The CBAM factor is 97.5% in 2026, declining to 51.5% in 2030 and 14% in 2033. This is the first year the phase-out mechanism creates a real demand signal by reducing the volume of allowances freely distributed to covered installations.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "The phase-out is already law and running. The 2.5% reduction in 2026 is modest in isolation but the trajectory is steep — by 2030 nearly half of current free allocation to these sectors will have been withdrawn. Watch annual verified emissions data from CBAM sectors to gauge how quickly the net demand effect compounds.",
        "source_label": "ICAP / European Commission",
        "source_url": "https://icapcarbonaction.com",
        "note_version": "",
    },
    {
        "event_id": "REG-027",
        "title": "UK ETS energy-from-waste voluntary monitoring phase",
        "jurisdiction": "UK",
        "instruments_affected": "UKA",
        "event_type": "Phase Change",
        "status": "Active",
        "next_date": "01/01/2028",
        "direction": "Bullish",
        "confidence": "High",
        "magnitude": "Medium",
        "summary": "UK ETS is expanding to include energy-from-waste and incineration plants. The voluntary monitoring phase began 1 January 2026 — operators measure, report, and verify emissions to the UK ETS Authority but incur no financial liability yet. Full compliance with surrender obligations begins 1 January 2028.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "New demand sector entering UK ETS from 2028. The voluntary monitoring phase now running is generating the verified emissions baseline that will determine the size of the demand increase. Watch monitoring data publications from the UK ETS Authority for early indicators of sector-wide emission volumes.",
        "source_label": "Norton Rose Fulbright / ICAP",
        "source_url": "https://icapcarbonaction.com",
        "note_version": "",
    },
    {
        "event_id": "REG-028",
        "title": "California LCFS first full compliance year under amended regulation",
        "jurisdiction": "California",
        "instruments_affected": "LCFS",
        "event_type": "Regulation",
        "status": "Active",
        "next_date": "15/05/2027",
        "direction": "Bullish",
        "confidence": "High",
        "magnitude": "Medium",
        "summary": "2026 is the first full compliance year under CARB's July 2025 amended LCFS regulation. New carbon intensity benchmarks are in effect: gasoline benchmark dropped from 85.77 to 76.60 gCO2e/MJ and diesel from 86.64 to 81.70. The regulation shifts to CA-GREET 4.0 for new pathway applications. The Auto-Acceleration Mechanism can tighten targets further if the credit bank remains oversupplied, with the earliest trigger date 15 May 2027.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "Tightening CI benchmarks will erode the existing credit bank over 2026. The pace of erosion determines whether the AAM triggers in 2027 — a further tightening catalyst. Watch quarterly CARB credit balance reports for bank drawdown trajectory. CA-GREET 4.0 transition affects which fuel pathways qualify for credit generation and may reduce supply from some existing projects.",
        "source_label": "Trinity Consultants / IETA",
        "source_url": "https://www.ieta.org",
        "note_version": "",
    },
    {
        "event_id": "REG-029",
        "title": "CORSIA Phase 1 end and Phase 2 transition",
        "jurisdiction": "ICAO",
        "instruments_affected": "CORSIA",
        "event_type": "Phase Change",
        "status": "Upcoming",
        "next_date": "31/12/2026",
        "direction": "Mixed",
        "confidence": "Medium",
        "magnitude": "Medium",
        "summary": "CORSIA mandatory Phase 1 (2024–2026) concludes at end of 2026, marking the first mandatory phase with real airline offsetting obligations for international emissions above the 2020 baseline. The scheme transitions to Phase 2 terms from 2027. Demand outlook through the end of Phase 1 is driven by a handful of major markets, and a supply crunch is emerging in CORSIA-eligible credits.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "Transition from Phase 1 to Phase 2 introduces uncertainty around baseline recalculation and eligible unit criteria for the new phase. Supply crunch in CORSIA-eligible credits is already visible — the pool of qualifying project vintages is constrained relative to projected Phase 1 offsetting demand. Watch ICAO Technical Advisory Body outputs on Phase 2 methodology and any changes to eligible fuels criteria.",
        "source_label": "cCarbon / ICAO",
        "source_url": "https://www.icao.int/environmental-protection/CORSIA",
        "note_version": "",
    },
    {
        "event_id": "REG-030",
        "title": "COP31 — Belém, Brazil",
        "jurisdiction": "Global",
        "instruments_affected": "VCM, CORSIA",
        "event_type": "Negotiation",
        "status": "Upcoming",
        "next_date": "2026-11",
        "direction": "Mixed",
        "confidence": "Low",
        "magnitude": "High",
        "summary": "COP31 takes place in Belém, Brazil in November 2026. Article 6 rules remain not fully settled following COP29. COP31 is the next major deadline for operationalising the Paris Agreement's international carbon market mechanisms (Article 6.2 bilateral agreements and Article 6.4 centralised mechanism). Outcome has direct read-across to CORSIA-eligible credit demand and voluntary market integrity frameworks.",
        "date_last_reviewed": "2026-03-19",
        "display": "TRUE",
        "analyst_note": "Article 6.4 supervisory body progress is the key variable — specifically whether the centralised mechanism begins issuing A6.4ERs at scale in time to influence the CORSIA-eligible supply pool. Bilateral Article 6.2 pipeline is already moving but quality and additionality of ITMOs remains contested. COP31 outcome will either accelerate or further delay the operationalisation timeline that VCM and CORSIA pricing depends on.",
        "source_label": "UNFCCC",
        "source_url": "https://unfccc.int",
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
    print(f"CB_add_events_023_030.py — {'APPLY' if apply else 'PREVIEW'} mode")
    print()

    print("Connecting to Google Sheets...")
    ws = connect_sheet()
    headers = ws.row_values(1)
    print(f"  Headers ({len(headers)}): {headers}")

    current_ids = [
        row[0] for row in ws.get_all_values()[1:] if row and row[0].strip()
    ]
    print(f"  Existing event IDs: {current_ids}")
    print()

    rows_to_append = []
    for ev in NEW_EVENTS:
        if ev["event_id"] in current_ids:
            print(f"  SKIP {ev['event_id']} — already in sheet")
            continue
        row = [ev.get(h, "") for h in headers]
        rows_to_append.append((ev["event_id"], ev["title"], row))

    if not rows_to_append:
        print("Nothing to add — all events already present.")
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
    parser = argparse.ArgumentParser(description="Append REG-023 to REG-030 to the Events sheet")
    parser.add_argument("--apply", action="store_true", help="Write to sheet (default is preview)")
    args = parser.parse_args()
    run(apply=args.apply)
