# CARBONsnaps — Session Brief

---

## Build workflow (current — updated 2026-03-19)

### Standard full refresh (new events added, content changed)

```bash
python3 CB_diff.py --apply
python3 CB_sync_regulatory.py --apply
python3 CB_update_scenarios.py --apply --stale-only
python3 CB_build.py && open index.html
```

### Cost-free rebuild (no new events, no content changes)

```bash
python3 CB_diff.py --apply
python3 CB_sync_regulatory.py --apply
python3 CB_build.py && open index.html
```

### UI/shell-only rebuild (no data changes at all)

```bash
python3 CB_build.py && open index.html
```

### When to run each script

| Script | Run when |
|---|---|
| `CB_diff.py --apply` | Every build — always first in sequence |
| `CB_sync_regulatory.py --apply` | Events tab in Sheet has changed |
| `CB_update_scenarios.py --apply --stale-only` | New events added, or content changed materially |
| `CB_update_scenarios.py --apply --force` | Full regeneration — new project, major content overhaul |
| `CB_build.py` | Any time — rebuilds index.html from current data.json and shell |

### `--stale-only` flag behaviour

An event's scenarios are regenerated if ANY of:
1. Scenarios are missing entirely
2. `generated_at` timestamp is absent
3. Scenarios are older than N days (default 7: `--stale-only`, custom: `--stale-only 14`)
4. `direction`, `status`, or `note_version` has changed since last generation (requires `scenarios_content_snapshot` to be present — absent on pre-flag builds, degrades gracefully to age-check only)

### Cost reference

- ~$0.10 per event scenario generated
- 30 events × $0.10 = ~$3.00 for a full forced regeneration
- Daily `--stale-only` builds: $0.00 if no content has changed

### Build output confirmed working (2026-03-19)

```
Instruments      : 8/8
Regulatory events: 30
Changelog entries: 0 (first run — will populate as events change)
Output           : index.html (262 KB)
```

Known warnings (non-blocking, expected):
- `[CORSIA] spark array is empty` — populate once price history source is wired up
- `[RIN] spark array is empty` — same
- `[45Z] spark array is empty` — same
- `[VCM] spark has only 3 points` — same
- `git add failed: fatal: not a git repository` — project not yet under git; ignore or init repo

---

## Regulatory tracker — current state (2026-03-19)

**30 events total. All have scenarios. Sheet has `note_version` column (all blank — start populating when analyst view genuinely changes).**

### Date format convention (source data)

- Fixed dates: `DD/MM/YYYY`
- Quarter estimates: `YYYY-QN`
- Half-year estimates: `YYYY-HN`
- Month-only estimates: `YYYY-MM`

### Date display (UI — updated session 2026-03-19)

All dates are converted to concrete calendar start-of-period dates in the table:
- `DD/MM/YYYY` → `30 Apr 2026` (hard date, no tilde)
- `2026-Q3` → `~1 Jul 2026` (estimated, italic + tilde prefix)
- `2026-H1` → `~1 Jan 2026`, `2026-H2` → `~1 Jul 2026`
- `2026-MM` → `~1 Mon YYYY`

**Urgency colour tiers** (table date cell):
- ≤30 days → red (`var(--hot)`)
- ≤90 days → amber (`var(--gold)`)
- Past + `status: Active` → green (`var(--green)`) with "Ongoing" sub-label
- Past + other → grey (`var(--text-lo)`)
- >90 days → default mid-grey

**Tooltip date sub-header** — shown inside the regulatory detail tooltip below the meta row:
- Concrete: `📅 Key date · 30 Apr 2026 · in 42d`
- Estimated: `📅 Key date · Q3 2026 · Earliest 1 Jul 2026 · in 3mo`
- Ongoing: `● Ongoing · started 1 Jan 2026`

**`parseSortDate` fix** — `DD/MM/YYYY` now correctly converted to `YYYY-MM-DD` for sorting. Previously all sheet-format dates sorted to end of queue.

### Events REG-001 to REG-015 — original tracker (added prior to 2026-03-19)

All have scenarios. Scenarios generated 2026-03-19. No `scenarios_content_snapshot` yet — will be written on next `--stale-only` run that triggers a regeneration.

### Events REG-016 to REG-022 — added 2026-03-19

| ID | Title | Instruments | Next Date | Direction |
|----|-------|-------------|-----------|-----------|
| REG-016 | EU ETS maritime 100% compliance phase-in | EUA | 01/01/2026 | Bullish |
| REG-017 | UK ETS Auction Reserve Price increase £22→£28 | UKA | 08/04/2026 | Bullish |
| REG-018 | UK ETS maritime expansion launch | UKA | 01/07/2026 | Bullish |
| REG-019 | EU ETS post-2030 Commission revision proposal | EUA | 2026-Q3 | Mixed |
| REG-020 | EU ETS post-2030 public consultation close | EUA | 04/05/2026 | Neutral |
| REG-021 | EU ETS annual surrender deadline (2025 emissions) | EUA | 30/04/2026 | Bullish |
| REG-022 | UK Carbon Border Adjustment Mechanism launch | UKA | 01/01/2027 | Bullish |

### Events REG-023 to REG-030 — added 2026-03-19

| ID | Title | Instruments | Next Date | Direction |
|----|-------|-------------|-----------|-----------|
| REG-023 | EU-UK ETS formal linking negotiations | UKA, EUA | 2026-Q4 | Bullish |
| REG-024 | EU ETS aviation stop-the-clock expiry and CORSIA assessment | EUA, CORSIA | 2026-H2 | Mixed |
| REG-025 | EU ETS Commission statutory review (July 2026) | EUA | 31/07/2026 | Mixed |
| REG-026 | EU ETS free allocation CBAM phase-out begins | EUA | 01/01/2026 | Bullish |
| REG-027 | UK ETS energy-from-waste voluntary monitoring phase | UKA | 01/01/2028 | Bullish |
| REG-028 | California LCFS first full compliance year under amended regulation | LCFS | 15/05/2027 | Bullish |
| REG-029 | CORSIA Phase 1 end and Phase 2 transition | CORSIA | 31/12/2026 | Mixed |
| REG-030 | COP31 — Belém, Brazil | VCM, CORSIA | 30/11/2026 | Mixed |

Note on REG-023: tracked as single "negotiations active" row. Add milestone rows (technical design, agreement in principle, ratification) when dates are confirmed.

---

## Pending items (priority order)

1. **Substack subscribe button** — create Substack account, add subscribe button/embed to CARBONsnaps site. First task next session. See Substack/digest roadmap below.

2. **Initialise git repo**: `cd ~/Downloads/CARBONsnaps && git init && git add . && git commit -m "init"`

3. **Evaluate Databento Standard ($199/month)** for automated EUA + UKA price feeds.

4. **Carbon markets primer** — "Carbon markets explained" section. Deferred — pocket until audience/product positioning is clearer. See also: `CB_market_relationships.html` built 2026-03-19.

5. **GDP stories audit** for CAN, FRA, ITA, BRA — content session, deferred.

---

## Completed items (session 2026-03-19, original)

- ✅ **Price context strip** — 52-week range bar with coloured dot per instrument in the instruments table.
- ✅ **Regulatory calendar view** — month-strip / horizontal timeline of upcoming events coloured by direction.
- ✅ **Strip three-level expertise toggle** — fully removed. App is expert-only.
- ✅ **Weather icons replaced with direction badges** — instruments table uses Bullish / Bearish / Mixed / Neutral badges throughout.
- ✅ **Decouple `DATA` from HTML build** — shell fetches `data.json` at runtime via `fetch('data.json')`.
- ✅ **Market relationships / linkage section** — interactive network diagram (`CB_market_relationships.html`). 9 nodes, 10 typed edges, click-to-highlight, per-instrument detail panel.

## Completed items (session 2026-03-19, continued)

- ✅ **Regulatory tracker date display** — all dates converted to concrete calendar start-of-period in the table. `~` prefix + italic for estimated (Q/H/month-only) formats. Urgency colour tiers. Relative countdown label (`in 12d`, `in 3mo`). `parseSortDate` fixed for `DD/MM/YYYY`.
- ✅ **Regulatory tooltip date sub-header** — detailed date metadata row inside the event detail tooltip, with estimated vs concrete vs ongoing variants.
- ✅ **Global story tooltips — headline** — tooltip title now shows `card.headline` from data (populated from `label` field). Fallback to `BRIEF_LABELS[idx]` if absent.
- ✅ **Global story tooltips — paragraph breaks** — body text split on sentence boundaries into `<p>` tags for readability. Scroll reset to top on every open.
- ✅ **Expertise level system fully purged** — `currentLevel` variable removed. `globalStories` restructured from `{beginner, moderate, expert}` to `{cards}`. All three files updated: `CB_data.json`, `CB_build.py`, `CB_carbonsnaps-shell.html`. `CB_build.py` now validates `globalStories.cards` and requires `headline` field on each card.
- ✅ **`globalStories.cards` — `headline` field added** — promoted from `label` in `CB_data.json`. All 3 expert cards updated. `CB_build.py` enforces `headline` as required field.
- ✅ **Glossary tooltips — hover on pointer devices** — replaced click-to-open with hover popover (150ms show delay, 200ms hide grace, positioned near term, flips above/below viewport). Touch devices retain click + centred modal + overlay. Detected via `window.matchMedia('(hover: hover) and (pointer: fine)')`.
- ✅ **Instrument tooltips — direction badge** — weather icon replaced with `Bullish / Bearish / Mixed / Neutral` badge, consistent with instruments table and regulatory tracker.
- ✅ **Instrument tooltips — paragraph breaks** — story text split via `splitBody()` into `<p>` tags. Scroll reset on open.

## Completed items (session 2026-03-19, this session)

- ✅ **Cite tag scrubbing** — `CB_update_scenarios.py` now strips `<cite>` tags from API responses before writing to `CB_data.json`. `re` module moved to top-level imports. `CB_scrub_citetags.py` one-off script written to clean existing stored scenarios.
- ✅ **Em-dash ban enforced in scenarios** — `CB_update_scenarios.py` replaces `—` with `, ` and `–` with `-` after cite tag strip, before JSON parse.
- ✅ **Changelog feature built** — `CB_diff.py` diffs current events against `last_state.json`, writes `changelog.json`. `CB_build.py` ingests `changelog.json` and bakes into `DATA.regulatory.changelog`. Shell renders gold collapsible banner above tracker showing changes this week, significance pills, from/to values. Clicking any entry opens event detail tooltip. Gold dot appears on updated rows in table and mobile cards. First run writes snapshot silently with no flood of entries.
- ✅ **Source attribution on global stories** — `bt-source` restyled to readable body font with separator line and `↗ Source:` prefix label.
- ✅ **Scenario confidence/magnitude display** — `Conf` and `Magnitude` tags rendered below "Scenarios" section label in event detail tooltip. Colour-coded green/gold/red by level. Only shown if fields present on event.
- ✅ **Deep-linking to events** — `?event=REG-017` in URL opens event detail tooltip on page load. URL updates on open, clears on close. Works on GitHub Pages (query param, not hash route).
- ✅ **Next 30 days strip** — compact digest of imminent events above the regulatory tracker. Same width as tracker (`max-width: 660px`). Red dot header, rows show date (red ≤14d, gold 15-30d), relative label, title, instruments, direction badge. Clicking row opens event detail tooltip. Absent when nothing in window. Respects instrument filter.
- ✅ **Instrument filter** — single click on instrument row highlights it, dims others, filters regulatory tracker and next 30 days strip to that instrument's events. Green filter badge with ✕ Clear appears above tracker. Click same row again or Clear to reset. Double-click or shift-click opens instrument detail tooltip.
- ✅ **Weather icon system fully removed** — `.wh-icon` CSS block removed. `sigEmoji()` and `emojiSignal()` functions removed. `signalToDir()` simplified: passes through direction words directly, retains legacy weather string map as silent fallback only. `_iconMap` removed from digest builder. `card.icon` removed from digest output.
- ✅ **Email digest (Substack)** — `Digest` button in Regulatory Tracker section header generates formatted plain-text weekly digest: this week's stories, changelog entries, next 30 days events. "Copy for Substack" button copies to clipboard. **Localhost-only**: button hidden on GitHub Pages via `location.protocol === 'file:'` / `location.hostname` check. Public never sees it.

---

## Instruments table — current column layout (updated 2026-03-19)

5 columns: **ID · Name · Price · 52W range bar · Policy price outlook badge**

- Vertical dividers between all columns
- Policy price outlook badge uses `reg-dir` CSS class
- 52W range bar: coloured dot (family accent colour) on a track, low/52W/high labels beneath. Falls back to "no data" for CORSIA, RIN, 45Z, VCM
- Table container: `max-width: 480px`
- Single click = toggle instrument filter on regulatory tracker. Double-click or shift-click = open instrument detail tooltip.

### `regulatory_signal` field

Computed mechanically by `CB_build.py` from direction values of upcoming regulatory events affecting each instrument. Valid values: `Bullish`, `Bearish`, `Mixed`, `Neutral`.

---

## `globalStories` data structure (updated 2026-03-19)

```json
{
  "globalStories": {
    "cards": [
      {
        "icon": "🔥",
        "label": "Compliance allowance selloff signals structural stress",
        "headline": "Compliance allowance selloff signals structural stress",
        "body": "...",
        "source": "..."
      }
    ],
    "last_updated": "2026-03-19"
  }
}
```

Required card fields (enforced by `CB_build.py`): `icon`, `label`, `headline`, `body`, `source`.

`headline` is the article-specific title shown at the top of the briefing tooltip. `label` is retained for backwards compatibility but `headline` takes precedence in the UI.

Note: `icon` field should always be an emoji (e.g. `"🔥"`), not a weather signal string. If a weather string (`"stormy"` etc.) is found in this field, it will render as text. Fix directly in `CB_data.json`.

---

## Changelog feature — current state (built 2026-03-19)

### Files

- **`CB_diff.py`** — diffs `CB_data.json` events against `last_state.json`, writes `changelog.json`. Run with `--apply` to write. Preview mode (no flag) prints diffs without writing.
- **`last_state.json`** — snapshot of all event fields from the previous build. Written by `CB_diff.py --apply` on every successful run.
- **`changelog.json`** — diff output. Keeps last 8 weeks of entries. Consumed by `CB_build.py`.
- **`CB_build.py`** — ingests `changelog.json`, injects as `DATA.regulatory.changelog` before baking into HTML.

### Tracked fields

`status`, `next_date`, `direction`, `note_version`

### Significance rules

- `high` — status changed, OR new event added, OR date within 60 days
- `medium` — analyst note updated (`note_version` bumped)
- `low` — all other field changes

### First-run behaviour

No `last_state.json` → writes initial snapshot, empty `changelog.json`. No flood of 30 "new event" entries.

### UI

Gold collapsible banner above tracker: `"N changes this week · N high-significance [Show ▼]"`. Expands to show: significance pill, event ID, change type, from→to, title. Row click opens event detail tooltip. Gold dot on updated rows (desktop table + mobile cards). Banner absent entirely when no changes in last 7 days.

---

## Substack / digest roadmap

### Concept

Weekly digest generated from live dashboard data — stories, changelog, next 30 days. Delivered by Substack. CARBONsnaps site is the production tool; Substack is the delivery mechanism.

### Phase 1 — Manual (current)

1. Run build, click Digest button (localhost only), copy text
2. Paste into Substack editor, tidy, publish
3. Add a simple "Subscribe" link on CARBONsnaps pointing to Substack page

**First task next session: create Substack account + add subscribe button to the site.**

### Phase 2 — Embedded subscribe form

Replace the outbound link with an email capture form embedded directly on CARBONsnaps. Substack provides embed code — one paste job. Readers subscribe without leaving the site.

### Phase 3 — Automated send (later)

Build pipeline generates digest and pushes to Substack via API. Review and send. Eventually fully automated.

### Platform choice: Substack

- Free to start, 10% of subscription revenue
- Built-in discovery network helps early growth
- Simple editor — plain text paste works well
- Switch to Beehiiv later if subscriber count justifies more tooling

---

## Glossary — current state (2026-03-19)

72 entries total. 22 original + 50 added session 2026-03-19. All in `CB_carbonsnaps-shell.html`. Linkify picks up all terms automatically on first occurrence.

**Hover behaviour (pointer devices):** 150ms show delay, 200ms hide grace period, popover positioned near term (280px wide, flips above/below). No overlay. Touch devices: click → centred modal with blackout overlay.

Categories: instruments, markets/schemes, regulatory bodies, policy mechanisms, carbon standards, project types, integrity frameworks, lifecycle methodology, units, California legislation, market terms.

Intentionally excluded: chemical symbols, AR4/AR5/AR6 (in GWP entry), RIN subcategories (in RIN/RFS entries), bare legislation citations, WTO/MFN/national treatment.

---

## Product strategy notes

### Direction: live dashboard

`DATA` is decoupled from HTML and fetched at runtime from `data.json`. Next step toward live dashboard is automated price feeds (see Databento evaluation in pending items).

### Expertise level

Three-level system fully removed from all files. App is expert-only. Do not reintroduce.

### Weather icon system

Fully removed. Direction is expressed exclusively in words: `Bullish`, `Bearish`, `Mixed`, `Neutral`. Do not reintroduce weather icons or signal strings anywhere.

### Em-dash ban

No em-dashes (`—`) anywhere in the app. `CB_update_scenarios.py` strips them at generation time. `CB_scrub_citetags.py` cleaned existing stored data. Enforce in any future content generation prompts.

### Audience

Not yet defined. Internal research tool vs subscriber product shapes all feature priorities. Decision deferred. Substack launch will inform this.

---

## Data APIs — research notes (2026-03-19)

### Recommended path

1. Automate EUA and UKA via **Databento Standard ($199/month)** — clean API, ICE-sourced OHLCV, no sales call.
2. Keep LCFS, RGGI, CCA, VCM on manual/semi-automated updates from public sources.
3. Hold off on OPIS and Xpansiv licences until clear commercial case.

### Cost estimates

| Scenario | Instruments | Est. monthly cost |
|---|---|---|
| Compliance only | EUA, UKA, CCA, RGGI | ~$199–500 |
| Compliance + clean fuel | Above + LCFS, Oregon CFP | ~$1,000–1,400 |
| All 8 instruments | All above + VCM | ~$2,200–3,400 |
| World's best | All above + ICE direct + BNEF | ~$10,000–18,000 |

### API options by instrument

**EUA, UKA, CCA, RGGI** — exchange-traded ICE futures:
- **Databento** — self-serve, $199/month Standard tier, ICE-sourced OHLCV
- **ICE direct** — authoritative but five-figure annual costs, not right entry point
- **Montel** — ~€5,000–20,000/year, more platform than raw API

**LCFS, RGGI assessments, clean fuel credits:**
- **OPIS (Dow Jones)** — ~$800–1,200/month entry-level, no self-serve API
- **S&P Global / Platts** — ~$20,000+/year entry point

**Voluntary carbon (GEO, N-GEO, CORSIA):**
- **Xpansiv Data** — ~$1,200–2,000/month, bespoke licence

**Research layer:**
- **Bloomberg Terminal + BNEF** — ~$2,250/month per seat + BNEF
