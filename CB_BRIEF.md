# CARBONsnaps — Session Brief

---

## Build workflow (current — updated 2026-03-22)

### Standard full refresh (new events added, content changed)

```bash
cd ~/Downloads/CARBONsnaps
python3 CB_diff.py --apply
python3 CB_sync_regulatory.py --apply
python3 CB_update_scenarios.py --apply --stale-only
python3 CB_update_stories.py --apply
python3 CB_build.py && open index.html
```

### Cost-free rebuild (no new events, no content changes)

```bash
cd ~/Downloads/CARBONsnaps
python3 CB_diff.py --apply
python3 CB_sync_regulatory.py --apply
python3 CB_update_stories.py --apply
python3 CB_build.py && open index.html
```

### UI/shell-only rebuild (no data changes at all)

```bash
python3 CB_build.py && open index.html
```

### After any local build — push to live site

```bash
git add -A && git commit -m "daily refresh $(date +%Y-%m-%d)" && git push
```

Cloudflare Pages auto-deploys within ~1 minute of push.

### When to run each script

| Script | Run when |
|---|---|
| `CB_diff.py --apply` | Every build — always first in sequence |
| `CB_sync_regulatory.py --apply` | Events tab in Sheet has changed |
| `CB_update_scenarios.py --apply --stale-only` | New events added, or content changed materially |
| `CB_update_scenarios.py --apply --force` | Full regeneration — new project, major content overhaul |
| `CB_update_stories.py --apply` | Every build — regenerates instrument stories and global cards |
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
- `CB_update_stories.py --apply`: ~$0.10–0.20/day (8 instrument stories + 3 global cards, ~9 API calls)

### Build output confirmed working (2026-03-22)

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

## Infrastructure — current state (updated 2026-03-22)

### Hosting

- **Live site**: `carbonsnaps.com` → Cloudflare Pages → GitHub repo `ralphlazar/CARBONsnaps`
- **Deployment**: automatic on every `git push` to `master`
- **Password gate**: `croc` / `Croc` — implemented in `CB_carbonsnaps-shell.html` so it survives rebuilds
- **Subscribe button**: in top bar, links to `carbonsnaps.substack.com`

### Git

- **Repo**: `github.com/ralphlazar/CARBONsnaps` (public)
- **Branch**: `master`
- **Local path**: `~/Downloads/CARBONsnaps`
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

1. **Add `ANTHROPIC_API_KEY` to `~/Desktop/.env`** — required for `CB_update_stories.py` to run. Get from [console.anthropic.com](https://console.anthropic.com). Console was down 2026-03-22 — check and add at next session.

2. **Test `CB_update_stories.py --apply`** — blocked by missing API key. Once key is in `.env`, run preview first, then apply.

3. **Build `CB_discover_events.py`** — web search script that surfaces new publicly-announced regulatory events not yet in the Sheet, for analyst review. Discussed 2026-03-22, not yet built.

4. **Evaluate Databento Standard ($199/month)** for automated EUA + UKA price feeds.

5. **Carbon markets primer** — "Carbon markets explained" section. Deferred — pocket until audience/product positioning is clearer. See also: `CB_market_relationships.html` built 2026-03-19.

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
- ✅ **Next 30 days strip** — compact digest of imminent events above the regulatory tracker. Same width as tracker (`max-width: 660px`). Red dot header, rows show date (red ≤14d, gold 15-30d), relative label, title, instruments, direction badge. Clicking row opens event detail tooltip. Absent when nothing in window.
- ✅ **Weather icon system fully removed** — `.wh-icon` CSS block removed. `sigEmoji()` and `emojiSignal()` functions removed. `signalToDir()` simplified: passes through direction words directly, retains legacy weather string map as silent fallback only. `_iconMap` removed from digest builder. `card.icon` removed from digest output.
- ✅ **Email digest (Substack)** — `Digest` button in Regulatory Tracker section header generates formatted plain-text weekly digest: this week's stories, changelog entries, next 30 days events. "Copy for Substack" button copies to clipboard. **Localhost-only**: button hidden on live site.

## Completed items (session 2026-03-20)

- ✅ **Git repo initialised** — `~/Downloads/CARBONsnaps` initialised, history clean of all secrets.
- ✅ **API key secured** — old Anthropic key revoked. New key stored in `~/Desktop/.env`. `CB_update_scenarios.py` updated to read from `Path.home() / "Desktop" / ".env"`.
- ✅ **Google credentials secured** — `CB_market-stats-key.json` added to `.gitignore`. Scrubbed from git history via `filter-branch`.
- ✅ **GitHub repo live** — `github.com/ralphlazar/CARBONsnaps`, public, master branch.
- ✅ **Cloudflare Pages hosting** — site live at `carbonsnaps.com` and `www.carbonsnaps.com`. Auto-deploys on push.
- ✅ **Password gate** — `croc` / `Croc`, implemented in `CB_carbonsnaps-shell.html` so it survives rebuilds.
- ✅ **Subscribe button** — in top bar, links to `carbonsnaps.substack.com`.
- ✅ **Google Cloud project created** — project `CARBONsnaps`, Sheets API enabled, service account `carbonsnaps-sheets` created, key downloaded, sheet shared with service account.
- ✅ **Substack account and publication** — account `ralphlazar`, publication CARBONsnaps at `carbonsnaps.substack.com`.
- ✅ **First Substack post published** — "CARBONsnaps — 20 March 2026", 2026-03-20.
- ✅ **Daily refresh ritual confirmed working** — all four scripts ran cleanly, site rebuilt and pushed.
- ✅ **Digest — rich-text clipboard copy** — "Copy for Substack" now writes `ClipboardItem` with both `text/html` and `text/plain`. Substack editor picks up HTML on paste. Falls back to plain text silently on unsupported browsers.
- ✅ **Digest — glossary hyperlinks** — `buildDigestHtml()` runs story bodies and event summaries through `linkifyDigest()`, which wraps first-occurrence glossary terms in `<a href="https://carbonsnaps.com/#gloss-{slug}">`. Titles/headlines left as plain text.
- ✅ **Glossary deep-link** — `glossSlug(term)` generates stable hash fragments (`eu-ets` → `#gloss-eu-ets`). `handleGlossHash()` fires on page load and `hashchange`, finds matching `GLOSSARY_TERMS` entry, opens centred modal. Wired into `init()` alongside existing `?event=` deep-link.
- ✅ **Glossary modal — null-anchor fix** — `openGlossTooltip(term, null)` now correctly opens centred modal on desktop (hover) devices. Previously the hover media query (`top:0;left:0;transform:none`) clobbered modal positioning. Fix: inline styles `top:50%;left:50%;transform:translate(-50%,-50%)` written explicitly in the modal branch, overriding the media query.

## Completed items (session 2026-03-22)

- ✅ **Instrument filter removed** — single click on instrument row now opens instrument detail tooltip (restored original behaviour). Filter logic (`setInstrumentFilter`, `activeInstrumentFilter`, filter badge, filter CSS classes) fully removed from `CB_carbonsnaps-shell.html`. Next 30 days strip always shows all events unfiltered. Decision: filter was undiscoverable and broke tooltip access; Option C (dedicated filter bar above tracker) deferred as future feature.
- ✅ **`CB_update_stories.py` built** — new daily script regenerates all instrument tooltip stories (`story.expert` field, all 8 instruments) and all 3 global story cards (`globalStories.cards`) via Anthropic API. Reads current price, change percentages, regulatory signal, and relevant upcoming events per instrument. Uses Claude claude-opus-4-5. Writes back to `CB_data.json`. Preview mode (no `--apply`) calls API but does not write. Cost ~$0.10-0.20/day.
- ✅ **Stray `.env` deleted** — `~/Downloads/CARBONsnaps/.env` deleted. Only canonical `.env` is `~/Desktop/.env`.

## Completed items (session 2026-03-23)

- ✅ **Subscribe button label** — updated to "SUBSCRIBE TO WEEKLY MAILOUT"
- ✅ **Mobile: subscribe button overlap fixed** — `position:absolute` overridden on mobile; button sits below header as full-width block
- ✅ **Mobile: regulatory tooltips fixed** — card click handlers were firing before cards were in the DOM; moved to after `innerHTML` assignment
- ✅ **"Weekly Edition" removed** — span deleted from top bar
- ✅ **Spark chart crosshair** — hover/touch on instrument tooltip spark chart shows vertical crosshair with price and date pill; flips left/right to stay in bounds
- ✅ **Footer nav built** — three buttons (WHAT?, HOW?, LEGALESE) each open a modal panel; closes on X or click outside
- ✅ **Footer modal content** — WHAT? and HOW? copy written and approved; LEGALESE contains Disclaimer and Privacy sections

## Session notes

- Claude: never issue `cp ~/Downloads/...` commands — user copies files manually.

---

## Instruments table — current column layout (updated 2026-03-22)

5 columns: **ID · Name · Price · 52W range bar · Policy price outlook badge**

- Vertical dividers between all columns
- Policy price outlook badge uses `reg-dir` CSS class
- 52W range bar: coloured dot (family accent colour) on a track, low/52W/high labels beneath. Falls back to "no data" for CORSIA, RIN, 45Z, VCM
- Table container: `max-width: 480px`
- **Single click = open instrument detail tooltip.** (Filter behaviour removed 2026-03-22.)

### `regulatory_signal` field

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
    "last_updated": "2026-03-22"
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
  "story_generated_at": "2026-03-22",
  "value_at_generation": 62.67
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

## Substack / digest — current state (updated 2026-03-20)

### Concept

Weekly digest generated from live dashboard data — stories, changelog, next 30 days. Delivered by Substack. CARBONsnaps site is the production tool; Substack is the delivery mechanism.

### Phase 1 — Manual (current)

1. Run build locally, click Digest button (localhost only), copy
2. Paste into Substack editor — HTML paste preserves glossary hyperlinks
3. Add title and subtitle manually, publish

### Weekly publishing workflow

1. `cd ~/Downloads/CARBONsnaps`
2. Run daily refresh ritual (diff → sync → scenarios → stories → build)
3. `open index.html` — click Digest button — Copy for Substack
4. Go to `carbonsnaps.substack.com/publish/home` → Create → Article
5. Paste content, add title (`CARBONsnaps — DD Month YYYY`) and subtitle
6. Publish → Everyone → Publish now
7. `git add -A && git commit -m "daily refresh YYYY-MM-DD" && git push`

### Digest HTML structure

`buildDigestHtml()` produces: `<h1>` title, `<h2>` subtitle, `<h3>` section headers, `<h4>` story headlines, `<p>` body paragraphs. Glossary terms in body text linked to `https://carbonsnaps.com/#gloss-{slug}`. Footer links to `https://carbonsnaps.com`.

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
