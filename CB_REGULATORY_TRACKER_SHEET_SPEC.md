# CB_REGULATORY_TRACKER_SHEET_SPEC.md
# CARBONsnaps — REGULATORY-TRACKER Google Sheet Specification
Last updated: Session 9 (2026-03-18)

---

## Sheet ID

`1Tvg30ZkRbomed3zVIx42DLcAAYVK9q50m4yX-hJwu68`

---

## Tab: Events

One row per regulatory event. `CB_sync_regulatory.py` reads this tab and writes
`display=TRUE` rows to `CB_data.json` under `data.regulatory.events[]`.

Column order is fixed. Do not insert, reorder, or rename columns without updating
`EXPECTED_HEADERS` in `CB_sync_regulatory.py`.

---

## Column reference

| Col | Field                 | Type            | Required | Controlled vocab / notes |
|-----|-----------------------|-----------------|----------|--------------------------|
| A   | `event_id`            | string          | Yes      | Unique. Snake_case. e.g. `eu_mcp_2026` |
| B   | `title`               | string          | Yes      | Short display title. No em-dashes. |
| C   | `jurisdiction`        | string          | Yes      | See Jurisdictions below |
| D   | `instruments_affected`| comma-separated | Yes      | See Instruments below. e.g. `EUA, UKA` |
| E   | `event_type`          | string          | Yes      | See Event Types below |
| F   | `status`              | string          | Yes      | See Statuses below |
| G   | `next_date`           | date or text    | No       | Preferred: `YYYY-MM-DD` or `DD/MM/YYYY`. Free text accepted for quarters/halves (e.g. `Q2 2026`, `H1 2026`). Used for display only — not sorted arithmetically if free text. |
| H   | `direction`           | string          | Yes      | `Bullish` / `Bearish` / `Neutral` / `Mixed` |
| I   | `confidence`          | string          | No       | `High` / `Medium` / `Low` |
| J   | `magnitude`           | string          | No       | `High` / `Medium` / `Low` |
| K   | `summary`             | string          | Yes      | 1–3 sentences. Plain text. No em-dashes. |
| L   | `date_last_reviewed`  | date            | No       | `YYYY-MM-DD` or `DD/MM/YYYY`. Active/Upcoming rows not reviewed in 30+ days trigger a stale warning. |
| M   | `display`             | boolean         | Yes      | `TRUE` to include in public output. `FALSE` to hide. |
| N   | `analyst_note`        | string          | No       | House view. "Our Read" framing. No attribution, no em-dashes. Rendered in detail tooltip. |
| O   | `source_label`        | string          | No       | Short human-readable citation. e.g. `European Commission, MRV Regulation 2024/573` or `CARB, 2024 LCFS Regulation Amendment, Dec 2023`. Rendered as footnote in detail tooltip. |
| P   | `source_url`          | string          | No       | Direct URL to primary source document (regulation text, government publication, official report). If present, `source_label` is wrapped in a link. Leave blank if not available. |

---

## Controlled vocabularies

### Jurisdictions
`EU` · `California` · `UK` · `US-Federal` · `ICAO` · `UN-Article6` · `Global` · `Australia` · `Canada` · `China` · `Other`

### Instruments
`EUA` · `CCA` · `UKA` · `CORSIA` · `LCFS` · `RIN` · `45Z` · `VCM`

### Event Types
`Consultation` · `Proposal` · `Vote` · `Implementation` · `Review` · `Election` · `Registry-Update` · `Court-Decision` · `Guidance` · `Cap Change` · `Rule Change` · `Regulation` · `Negotiation` · `Phase Change` · `Price Floor`

### Statuses
`Upcoming` · `Active` · `Decided` · `Delayed` · `Withdrawn`

### Directions
`Bullish` · `Bearish` · `Neutral` · `Mixed`

### Confidence / Magnitude
`High` · `Medium` · `Low`

---

## Stale warning logic

`CB_sync_regulatory.py` issues a `[STALE]` warning for any row where:
- `status` is `Active` or `Upcoming`, AND
- `date_last_reviewed` is more than 30 days ago, OR `date_last_reviewed` is blank

Stale event IDs are written to `data.regulatory.stale_warnings[]` and the script
exits with code 1 if any stale rows are present.

---

## Pipeline notes

- `CB_sync_regulatory.py` runs in **preview mode** by default (prints diff, no writes).
- Pass `--apply` to write to `CB_data.json`.
- Only `display=TRUE` rows are written to `data.json`. All rows are validated regardless.
- Rows with any `[ERROR]` are excluded from output even if `display=TRUE`.
- `source_label` and `source_url` are passed through as-is. No URL validation is performed by the sync script.
