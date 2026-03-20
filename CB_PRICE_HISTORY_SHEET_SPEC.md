# CB_PRICE_HISTORY_SHEET_SPEC.md
# CARBONsnaps Price History Sheet Spec

Last updated: March 18, 2026

---

## Overview

Two new tabs in the existing REGULATORY-TRACKER Google Sheet:

| Tab | Written by | Purpose |
|-----|------------|---------|
| `PRICE-HISTORY-AUTO` | `CB_fetch_market_data.py` | Auto-fetched daily closes (yfinance). Do not edit manually. |
| `PRICE-HISTORY-MANUAL` | You, manually | Manually entered closes for instruments with no free data feed. |

Both tabs use the same column schema. The sync script (`CB_sync_sheet.py`) reads both and merges them. **Manual tab wins over auto tab on the same instrument + date** — use this to correct any bad auto value.

---

## Column schema (both tabs)

| Column | Type | Required | Format | Notes |
|--------|------|----------|--------|-------|
| `date` | String | Yes | `YYYY-MM-DD` | Trading day (not a Google Sheets date cell — plain text). |
| `instrument_id` | String | Yes | Must match exactly | One of: `EUA` `CCA` `UKA` `CORSIA` `LCFS` `RIN` `45Z` `VCM` |
| `close` | Number | Yes | Float | Settlement or close price. No currency symbols. |
| `currency` | String | Yes | `EUR` / `USD` / `GBP` | Per-instrument currency (see table below). |
| `source` | String | No | Free text | e.g. `CARB-quarterly`, `manual`, `yfinance:EUA=F` |

### Currency per instrument

| Instrument | Currency |
|------------|----------|
| EUA | EUR |
| CCA | USD |
| UKA | GBP |
| CORSIA | USD |
| LCFS | USD |
| RIN | USD |
| 45Z | USD |
| VCM | USD |

---

## PRICE-HISTORY-AUTO

This tab is **owned and overwritten by `CB_fetch_market_data.py`**. Do not edit it by hand. If you need to correct a value, add an override row to PRICE-HISTORY-MANUAL instead.

Currently fetches: **EUA only** (via `yfinance:EUA=F`, 36 months of daily closes).

To add more instruments via yfinance in future, add entries to `YFINANCE_INSTRUMENTS` in `CB_fetch_market_data.py`.

---

## PRICE-HISTORY-MANUAL

This tab is maintained by hand. Add a row for any price you want to record or correct.

### Instruments to populate manually

These instruments have no free daily price feed. Enter data here as you source it.

| Instrument | Suggested sources | Suggested frequency |
|------------|-------------------|---------------------|
| CCA | CARB quarterly auction results (arb.ca.gov), OPIS, Argus | Quarterly or when available |
| UKA | DESNZ auction results (gov.uk), ICE end-of-day | Weekly or when available |
| CORSIA | ICAO reports, broker indications | Monthly or when available |
| LCFS | CARB LCFS quarterly weighted average price report | Quarterly |
| RIN | EPA EMTS transaction data, Argus | Weekly or when available |
| 45Z | IRS guidance, broker indications (no market price yet) | As available |
| VCM | Xpansiv CBL index, Ecosystem Marketplace reports | Monthly or when available |

### Notes on manual entry

- Use the closest available settlement or average price for the date.
- For quarterly averages (CARB LCFS, CARB CCA auctions), use the last day of the quarter as the date.
- The `source` column is free text — use it to record where the number came from (e.g. `CARB-LCFS-Q4-2025-report`, `ICAO-Jan2026-brief`).
- Do not leave `close` blank. If you do not have a price for a date, omit the row entirely.
- Dates must be in `YYYY-MM-DD` plain text format. Do not use Google Sheets date formatting on this column.

### Example rows

```
date         instrument_id  close   currency  source
2025-12-31   CCA            30.15   USD       CARB-auction-Q4-2025
2025-12-31   LCFS           58.40   USD       CARB-LCFS-Q4-2025-report
2025-12-31   UKA            34.20   GBP       DESNZ-auction-Dec2025
2026-01-15   CORSIA         6.20    USD       broker-indication-Jan2026
2026-01-31   VCM            4.60    USD       CBL-nature-index-Jan2026
```

---

## How the merge works

`CB_sync_sheet.py` reads both tabs and merges rows by `(instrument_id, date)`. Manual rows overwrite auto rows on the same instrument + date. Both tabs are read in full on every sync run — no incremental logic.

---

## Setup steps (one time)

1. Open the REGULATORY-TRACKER Google Sheet.
2. Add a new tab named `PRICE-HISTORY-AUTO` with the header row:
   ```
   date | instrument_id | close | currency | source
   ```
   Leave it otherwise empty. `CB_fetch_market_data.py --apply` will populate it.

3. Add a new tab named `PRICE-HISTORY-MANUAL` with the same header row.
   Start adding manual rows as you source data for the non-auto instruments.

4. Ensure the service account (`CB_market-stats-key.json`) has Editor access
   to the sheet (required for `CB_fetch_market_data.py` to write to PRICE-HISTORY-AUTO).
   Read-only access is sufficient for `CB_sync_sheet.py`.

---

## Run order

```bash
# 1. Fetch new EUA data from yfinance -> PRICE-HISTORY-AUTO
python3 CB_fetch_market_data.py --apply

# 2. Sync all price history -> CB_data.json (prices, sparks, change fields)
python3 CB_sync_sheet.py --apply

# 3. Refresh instrument stories (required if prices changed — clears VAG warnings)
python3 CB_update_stories.py --apply     # not yet built

# 4. Build index.html
python3 CB_build.py
```

Exit codes for `CB_sync_sheet.py`:
- `0` — success, no value_at_generation mismatches
- `1` — fatal error (sheet not found, bad data)
- `2` — success but value_at_generation mismatches exist (CB_build.py will abort until stories are refreshed)
