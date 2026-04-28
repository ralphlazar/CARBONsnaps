# CARBONsnaps — Session Brief

---

## Build workflow (current — updated 2026-04-09)

### Standard full refresh (weekly ritual — includes price update)

```bash
cd /Users/lisaswerling/RALPH/AI/CARBONsnaps
python3 CB_fetch_market_data.py --apply
python3 CB_sync_sheet.py --apply
python3 CB_diff.py --apply
python3 CB_sync_regulatory.py --apply
python3 CB_update_scenarios.py --apply --stale-only
python3 CB_update_stories.py --apply
python3 CB_build.py && open index.html
```

**Important ordering rules:**
- `CB_fetch_market_data.py` must run before `CB_sync_sheet.py`
- `CB_sync_sheet.py` must run before `CB_update_stories.py` (price change triggers `value_at_generation` mismatch guard — stories resolves it)
- `CB_update_stories.py` must run before `CB_build.py` when prices have changed

### Cost-free rebuild (no new events, no content changes)

```bash
cd /Users/lisaswerling/RALPH/AI/CARBONsnaps
python3 CB_fetch_market_data.py --apply
python3 CB_sync_sheet.py --apply
python3 CB_diff.py --apply
python3 CB_sync_regulatory.py --apply
python3 CB_update_stories.py --apply
python3 CB_build.py && open index.html
```

### UI/shell-only rebuild (no data changes at all)

```bash
python3 CB_build.py && open index.html
```

### After Claude delivers a modified shell file

Always provide both of these bash blocks after delivering any updated `CB_carbonsnaps-shell.html`:

```bash
cp ~/Downloads/CB_carbonsnaps-shell.html /Users/lisaswerling/RALPH/AI/CARBONsnaps/CB_carbonsnaps-shell.html
```

```bash
cd /Users/lisaswerling/RALPH/AI/CARBONsnaps && python3 CB_build.py && open index.html
```

### After any local build — push to live site

```bash
git add -A && git commit -m "weekly refresh $(date +%Y-%m-%d)" && git push
```

Cloudflare Pages auto-deploys within ~1 minute of push.

### When to run each script

| Script | Run when |
|---|---|
| `CB_fetch_market_data.py --apply` | Every ritual — fetches EUA prices from yfinance → Google Sheet |
| `CB_sync_sheet.py --apply` | Every ritual — Sheet price history → CB_data.json (price, change_1w/1m/3m, spark, last_updated) |
| `CB_diff.py --apply` | Every build — always first in regulatory sequence |
| `CB_sync_regulatory.py --apply` | Events tab in Sheet has changed |
| `CB_update_scenarios.py --apply --stale-only` | New events added, or content changed materially |
| `CB_update_scenarios.py --apply --force` | Full regeneration — new project, major content overhaul |
| `CB_update_stories.py --apply` | Every build — regenerates instrument stories and global cards; must run after CB_sync_sheet.py when prices changed |
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
- Weekly `--stale-only` builds: $0.00 if no content has changed
- `CB_update_stories.py --apply`: ~$0.10–0.20/run (8 instrument stories + 3 global cards, ~9 API calls)

### Build output confirmed working (2026-04-09)

```
Instruments      : 8/8
Regulatory events: 30
Changelog entries: 0
Output           : index.html
```

Known warnings (non-blocking, expected):
- `[CORSIA] spark array is empty` — populate once price history source is wired up
- `[RIN] spark array is empty` — same
- `[45Z] spark array is empty` — same
- `[VCM] spark has only 3 points` — same

---

## Price data pipeline — current state (updated 2026-04-09)

### Scripts

- **`CB_fetch_market_data.py`** — fetch layer. Contacts yfinance, writes 36 months of daily closes to `PRICE-HISTORY-AUTO` tab in Google Sheet. Never reads/writes `CB_data.json`.
- **`CB_sync_sheet.py`** — sync layer. Reads `PRICE-HISTORY-AUTO` (auto) and `PRICE-HISTORY-MANUAL` tabs, writes `price`, `change_1w`, `change_1m`, `change_3m`, `spark`, `last_updated` into `CB_data.json`. Never contacts external APIs.

### Merge rule

`PRICE-HISTORY-MANUAL` wins over `PRICE-HISTORY-AUTO` on the same instrument + date. Use the manual tab to correct or override any auto row.

### Instruments with automated price fetch (yfinance)

| Instrument | Ticker | Currency |
|---|---|---|
| EUA | CO2.L | GBP |

### Instruments on manual price entry (PRICE-HISTORY-MANUAL tab)

CCA, UKA, LCFS, VCM — updated manually in Google Sheet. CORSIA, RIN, 45Z — no price history yet.

### `value_at_generation` guard

`CB_sync_sheet.py` warns when a price update would cause a mismatch with `value_at_generation`. This is expected — always run `CB_update_stories.py --apply` after `CB_sync_sheet.py` and before `CB_build.py`. Build will abort if mismatch exists.

---

## Infrastructure — current state (updated 2026-04-09)

### Hosting

- **Live site**: `carbonsnaps.com` → Cloudflare Pages → GitHub repo `ralphlazar/CARBONsnaps`
- **Deployment**: automatic on every `git push` to `master`
- **Password gate**: `croc` / `Croc` — implemented in `CB_carbonsnaps-shell.html` so it survives rebuilds
- **Subscribe button**: in top bar, links to `carbonsnaps.substack.com`

### Git

- **Repo**: `github.com/ralphlazar/CARBONsnaps` (public)
- **Branch**: `master`
- **Local path**: `/Users/lisaswerling/RALPH/AI/CARBONsnaps`
- **Remote**: `origin` → GitHub

### Secrets / credentials

- **`.env` location**: `~/Desktop/.env` — never inside project folder, never committed
- **`.env` contents**:
  - `ANTHROPIC_API_KEY` — Anthropic API key. **Must be present for `CB_update_stories.py` and `CB_update_scenarios.py` to work.** Key is NOT auto-loaded from environment — it must be explicitly in this file.
  - `REGULATORY_SHEET_ID=1Tvg30ZkRbomed3zVIx42DLcAAYVK9q50m4yX-hJwu68`
  - `PRICE_HISTORY_SHEET_ID` — not yet set up
  - `FRED_API_KEY` — not yet added (needed by CARBONsnaps; add when scripts use it)
- **`.env` parse convention** (all scripts): strip quotes from values (`.strip('"').strip("'")`), load at module level before any other logic
- **Stray `.env` files**: only `~/Desktop/.env` is canonical. Any `.env` inside the project folder should be deleted — it is not read and causes confusion.
- **Google service account**: `carbonsnaps-sheets@carbonsnaps.iam.gserviceaccount.com`
  - Key file: `CB_market-stats-key.json` in project folder — gitignored
  - Google Cloud project: `CARBONsnaps` (project ID: `carbonsnaps`)
  - Sheets API enabled on this project
  - Service account has Editor access to the regulatory Google Sheet

### Domain

- **Registrar**: Cloudflare (`carbonsnaps.com` registered 2026-03-20)
- **DNS**: managed by Cloudflare
- `carbonsnaps.com` → Cloudflare Pages (CNAME record, active)
- `www.carbonsnaps.com` → Cloudflare Pages (active)
- `newsletter.carbonsnaps.com` — not yet set up (deferred — Substack charges $50 for custom domain; revisit when subscriber count justifies)

### Substack

- **Account**: `ralphlazar` (personal author account, spans all projects)
- **Publication**: CARBONsnaps at `carbonsnaps.substack.com`
- **First post published**: 2026-03-20
- **Phase**: Manual digest — run build locally, click Digest button, copy, paste into Substack, add title/subtitle, publish
- **Digest button**: localhost-only — visible when opening `index.html` as a local file, hidden on live site

---

## Regulatory tracker — current state (2026-03-22)

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

1. **Build `CB_discover_events.py`** — not yet built. Planned: use Anthropic API with web search tool to surface new regulatory events across all 8 instruments; deduplicate against existing REG-001 onwards; print candidates with proposed field values (title, instruments, date, direction, note) for review; on confirmation auto-assign next REG-0XX IDs and append to Google Sheet. Run ad hoc.

2. **Evaluate Databento Standard ($199/month)** for automated EUA + UKA price feeds. Currently EUA is automated via yfinance (CO2.L ETF proxy); UKA has no automated feed.

3. **Carbon markets primer** — "Carbon markets explained" section. Deferred — pocket until audience/product positioning is clearer. See also: `CB_market_relationships.html` built 2026-03-19.

---

## Bug fixes applied (2026-04-09)

### `CB_build.py` — `_meta.generated` date was always one day stale

**Root cause**: `CB_build.py` stamped `_meta.generated = TODAY` in `CB_data.json` *after* the data had already been serialised and inlined into `index.html`. The HTML always contained yesterday's date.

**Fix**: moved the `_meta` stamp to *before* `json.dumps(data)`, so the correct date is baked into the inlined payload. The subsequent write to `CB_data.json` retains the stamp but no longer duplicates it.

---

## `regulatory_signal` field

Computed mechanically by `CB_build.py` from direction values of upcoming regulatory events affecting each instrument. Valid values: `Bullish`, `Bearish`, `Mixed`, `Neutral`.

---

## `globalStories` data structure (updated 2026-03-22)

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
    "last_updated": "2026-04-09"
  }
}
```

Required card fields (enforced by `CB_build.py`): `icon`, `label`, `headline`, `body`, `source`.

`headline` is the article-specific title shown at the top of the briefing tooltip. `label` is retained for backwards compatibility but `headline` takes precedence in the UI.

Note: `icon` field should always be an emoji (e.g. `"🔥"`), not a weather signal string. If a weather string (`"stormy"` etc.) is found in this field, it will render as text. Fix directly in `CB_data.json`.

Cards are regenerated daily by `CB_update_stories.py --apply`. Do not manually edit `globalStories.cards` in `CB_data.json` — changes will be overwritten on next run.

---

## `instrument.story` data structure (updated 2026-03-22)

```json
{
  "story": {
    "expert": "..."
  },
  "story_generated_at": "2026-04-09",
  "value_at_generation": 67.66
}
```

`story.expert` is the paragraph shown in the instrument detail tooltip. Regenerated daily by `CB_update_stories.py --apply`. The `beginner` and `moderate` keys may still exist on older instruments — they are ignored by the UI (expert-only app).

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

## Substack / digest — current state (updated 2026-04-09)

### Concept

Weekly digest generated from live dashboard data — stories, changelog, next 30 days. Delivered by Substack. CARBONsnaps site is the production tool; Substack is the delivery mechanism.

### Phase 1 — Manual (current)

1. Run build locally, click Digest button (localhost only), copy
2. Paste into Substack editor — HTML paste preserves glossary hyperlinks
3. Add title and subtitle manually, publish

### Weekly publishing workflow

1. `cd /Users/lisaswerling/RALPH/AI/CARBONsnaps`
2. Run full weekly ritual (fetch → sync sheet → diff → sync regulatory → scenarios → stories → build)
3. `open index.html` — click Digest button — Copy for Substack
4. Go to `carbonsnaps.substack.com/publish/home` → Create → Article
5. Paste content, add title (`CARBONsnaps — DD Month YYYY`) and subtitle
6. Publish → Everyone → Publish now
7. `git add -A && git commit -m "weekly refresh YYYY-MM-DD" && git push`

### Digest HTML structure

`buildDigestHtml()` produces: `<h1>` title, `<h2>` subtitle, `<h3>` section headers, `<h4>` story headlines, `<p>` body paragraphs. Glossary terms in body text linked to `https://carbonsnaps.com/#gloss-{slug}`. Footer links to `https://carbonsnaps.com`.

Digest title date is derived from `DATA._meta.generated` (now correctly stamped at build time).

### Phase 2 — Automated send (later)

Build pipeline generates digest and pushes to Substack via API.

### Platform

Substack free tier. 10% of subscription revenue when paid tiers enabled. Switch to Beehiiv if subscriber count justifies more tooling.

---

## Glossary — current state (updated 2026-03-20)

72 entries total. 22 original + 50 added session 2026-03-19. All in `CB_carbonsnaps-shell.html`. Linkify picks up all terms automatically on first occurrence.

**Hover behaviour (pointer devices):** 150ms show delay, 200ms hide grace period, popover positioned near term (280px wide, flips above/below). No overlay. Touch devices: click → centred modal with blackout overlay.

**Deep-link behaviour:** `https://carbonsnaps.com/#gloss-{slug}` opens the matching glossary entry as a centred modal on any device. Hash fired on page load and `hashchange`. Used in Substack digest links.

**Slug format:** `glossSlug(term)` — lowercase, spaces to hyphens, non-alphanumeric stripped. Examples: `"EU ETS"` → `#gloss-eu-ets`, `"Cap-and-trade"` → `#gloss-cap-and-trade`, `"45Z"` → `#gloss-45z`.

Categories: instruments, markets/schemes, regulatory bodies, policy mechanisms, carbon standards, project types, integrity frameworks, lifecycle methodology, units, California legislation, market terms.

Intentionally excluded: chemical symbols, AR4/AR5/AR6 (in GWP entry), RIN subcategories (in RIN/RFS entries), bare legislation citations, WTO/MFN/national treatment.

---

## Footer — current state (updated 2026-04-09)

Footer contains: nav buttons (WHAT? / HOW? / LEGALESE), CARBONsnaps brand, build date / version meta, and "Powered by MacroSnaps" link to `https://macrosnaps.app/`. All footer text uses `var(--font-display)`, 9px, uppercase, `var(--text-lo)`. Links use `var(--green)`. Styled via `.footer-powered` class in `CB_carbonsnaps-shell.html`.

---

## Product strategy notes

### Direction: live dashboard

`DATA` is decoupled from HTML and fetched at runtime from `data.json`. Next step toward live dashboard is automated price feeds (see Databento evaluation in pending items).

### Expertise level

Three-level system fully removed from all files. App is expert-only. Do not reintroduce.

### Weather icon system

Fully removed. Direction is expressed exclusively in words: `Bullish`, `Bearish`, `Mixed`, `Neutral`. Do not reintroduce weather icons or signal strings anywhere.

### Em-dash ban

No em-dashes (`—`) anywhere in the app. `CB_update_scenarios.py` strips them at generation time. `CB_scrub_citetags.py` cleaned existing stored data. `CB_update_stories.py` strips them at generation time. Enforce in any future content generation prompts.

### Instrument filter

Removed 2026-03-22. Single click on instrument row opens tooltip. Future Option C (filter bar above tracker) deferred — implement when UI complexity justifies it.

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
