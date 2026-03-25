#!/usr/bin/env python3
"""
CB_update_stories.py
Regenerates instrument tooltip stories and global story cards from live price
and regulatory data. Run after CB_sync_regulatory.py in the daily ritual.

Usage:
  python3 CB_update_stories.py           # preview — prints output, no write
  python3 CB_update_stories.py --apply   # writes back to CB_data.json
"""

import json
import sys
import os
import re
from pathlib import Path
from datetime import date, datetime

# ── Config ────────────────────────────────────────────────────────────────────

DATA_PATH   = Path(__file__).parent / "CB_data.json"
MODEL       = "claude-opus-4-5"
MAX_TOKENS  = 800
APPLY       = "--apply" in sys.argv

# Load .env from Desktop (matches CB_update_scenarios.py convention)
_env_path = Path.home() / "Desktop" / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

# ── Helpers ───────────────────────────────────────────────────────────────────

def scrub(text):
    """Remove em-dashes and tidy whitespace."""
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def call_claude(prompt, max_tokens=MAX_TOKENS):
    import urllib.request
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY not set")
        sys.exit(1)
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return scrub(data["content"][0]["text"])

def days_until(date_str):
    """Return days until a date string, or None."""
    try:
        if re.match(r"\d{2}/\d{2}/\d{4}", date_str):
            d = datetime.strptime(date_str, "%d/%m/%Y").date()
        elif re.match(r"\d{4}-Q\d", date_str):
            q = int(date_str[-1])
            d = date(int(date_str[:4]), (q - 1) * 3 + 1, 1)
        elif re.match(r"\d{4}-H\d", date_str):
            h = int(date_str[-1])
            d = date(int(date_str[:4]), 1 if h == 1 else 7, 1)
        elif re.match(r"\d{4}-\d{2}", date_str):
            d = datetime.strptime(date_str, "%Y-%m").date().replace(day=1)
        else:
            return None
        return (d - date.today()).days
    except Exception:
        return None

# ── Instrument story prompt ───────────────────────────────────────────────────

def build_instrument_prompt(inst, reg_events):
    iid = inst["id"]

    # Relevant regulatory events for this instrument
    rel_events = [
        e for e in reg_events
        if iid in (
            e["instruments_affected"]
            if isinstance(e["instruments_affected"], list)
            else [e["instruments_affected"]]
        )
    ]

    # Sort: upcoming first, then active, then past
    def event_sort_key(e):
        d = days_until(e.get("next_date", ""))
        return d if d is not None else 9999

    rel_events.sort(key=event_sort_key)

    event_lines = []
    for e in rel_events[:6]:
        d = days_until(e.get("next_date", ""))
        timing = f"in {d}d" if d is not None and d >= 0 else ("ongoing" if e.get("status") == "Active" else "past")
        event_lines.append(
            f"  - {e['title']} ({timing}, {e['direction']}, {e['status']}): {e.get('analyst_note','')[:180]}"
        )
    events_block = "\n".join(event_lines) if event_lines else "  None"

    price_str = f"{inst['price']} {inst['price_unit']}" if inst.get("price") and inst["price"] != "-" else "no current price"
    changes = []
    if inst.get("change_1w"): changes.append(f"1w: {inst['change_1w']}")
    if inst.get("change_1m"): changes.append(f"1m: {inst['change_1m']}")
    if inst.get("change_3m"): changes.append(f"3m: {inst['change_3m']}")
    change_str = ", ".join(changes) if changes else "no price history"

    return f"""You are the analyst behind CARBONsnaps, a professional carbon and clean fuel credit intelligence service. Write the instrument briefing for {inst['name']} ({iid}).

INSTRUMENT DATA (as of today, {date.today().isoformat()}):
  Price: {price_str}
  Price changes: {change_str}
  Regulatory signal: {inst['regulatory_signal']}
  Regulatory note: {inst.get('regulatory_note', '')}
  Description: {inst.get('description', '')[:300]}

RELEVANT REGULATORY EVENTS:
{events_block}

Write a single expert-level briefing paragraph (4-6 sentences, ~120-180 words). Rules:
- Expert audience: institutional traders, carbon market analysts, compliance officers
- Lead with the most significant price action or structural dynamic right now
- Connect price behaviour to specific regulatory drivers from the events above
- Name specific mechanisms, timelines, and thresholds where relevant
- End with a forward-looking statement about what to watch
- No em-dashes (use commas or semicolons instead)
- No bullet points, headers, or markdown
- No "as of today" or date references in the text
- Tone: precise, unsentimental, direct

Output the paragraph only. No preamble."""

# ── Global stories prompt ─────────────────────────────────────────────────────

def build_global_stories_prompt(instruments, reg_events):
    inst_lines = []
    for inst in instruments:
        price_str = f"{inst['price']} {inst['price_unit']}" if inst.get("price") and inst["price"] != "-" else "no price"
        changes = []
        if inst.get("change_1w"): changes.append(f"1w {inst['change_1w']}")
        if inst.get("change_3m"): changes.append(f"3m {inst['change_3m']}")
        inst_lines.append(f"  {inst['id']} ({inst['name']}): {price_str} | {', '.join(changes)} | signal: {inst['regulatory_signal']}")

    # Upcoming events within 90 days
    upcoming = []
    for e in reg_events:
        d = days_until(e.get("next_date", ""))
        if d is not None and 0 <= d <= 90:
            upcoming.append(f"  - {e['title']} (in {d}d, {e['direction']}): {e.get('analyst_note','')[:120]}")
    upcoming_block = "\n".join(upcoming[:8]) if upcoming else "  None in next 90 days"

    return f"""You are the analyst behind CARBONsnaps. Write exactly 3 global market story cards for this week's edition.

MARKET DATA (as of {date.today().isoformat()}):
{chr(10).join(inst_lines)}

UPCOMING REGULATORY EVENTS (next 90 days):
{upcoming_block}

Each card must:
- Cover a distinct cross-instrument theme or a single dominant instrument story
- Have a headline (max 8 words, punchy and specific)
- Have a body (5-8 sentences, ~150-200 words) — expert-level, institutional audience
- Have a source string (comma-separated data sources cited, no URLs)
- Have an icon (single emoji only)

Rules:
- No em-dashes anywhere (use commas or semicolons)
- No bullet points or markdown in body text
- No "as of today" or date references in body text
- Cover different parts of the market across the 3 cards (do not write 3 EUA cards)
- Tone: precise, analytical, unsentimental

Return ONLY valid JSON in this exact structure, no preamble or trailing text:
[
  {{
    "icon": "emoji",
    "headline": "Headline text here",
    "label": "Headline text here",
    "body": "Body text here.",
    "source": "Source 1, Source 2"
  }},
  {{
    "icon": "emoji",
    "headline": "Headline text here",
    "label": "Headline text here",
    "body": "Body text here.",
    "source": "Source 1, Source 2"
  }},
  {{
    "icon": "emoji",
    "headline": "Headline text here",
    "label": "Headline text here",
    "body": "Body text here.",
    "source": "Source 1, Source 2"
  }}
]"""

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print(f"  CB_update_stories.py — {'APPLY' if APPLY else 'PREVIEW'} mode")
    print(f"  {date.today().isoformat()}")
    print("=" * 60)

    data = json.loads(DATA_PATH.read_text())
    instruments = data["instruments"]
    reg_events  = data["regulatory"]["events"]
    today_str   = date.today().isoformat()

    # ── 1. Instrument stories ──────────────────────────────────────────────
    print("\n-- Instrument stories " + "-" * 38)

    for inst in instruments:
        iid = inst["id"]
        print(f"  [{iid}] generating...", end="", flush=True)
        prompt = build_instrument_prompt(inst, reg_events)
        try:
            text = call_claude(prompt)
            if APPLY:
                # Preserve structure, update expert only
                if not isinstance(inst.get("story"), dict):
                    inst["story"] = {}
                inst["story"]["expert"] = text
                inst["value_at_generation"] = inst.get("price")
                inst["story_generated_at"] = today_str
            print(f" done ({len(text.split())} words)")
            if not APPLY:
                print(f"    PREVIEW: {text[:120]}...")
        except Exception as ex:
            print(f" ERROR: {ex}")

    # ── 2. Global story cards ──────────────────────────────────────────────
    print("\n-- Global story cards " + "-" * 38)
    print("  Generating 3 cards...", end="", flush=True)

    prompt = build_global_stories_prompt(instruments, reg_events)
    try:
        raw = call_claude(prompt, max_tokens=1600)
        # Strip any accidental markdown fences
        raw = re.sub(r"^```[a-z]*\n?", "", raw.strip())
        raw = re.sub(r"\n?```$", "", raw.strip())
        cards = json.loads(raw)
        # Scrub all text fields
        for card in cards:
            for field in ("headline", "label", "body", "source"):
                if field in card:
                    card[field] = scrub(card[field])
        print(f" done ({len(cards)} cards)")
        if APPLY:
            data["globalStories"]["cards"]        = cards
            data["globalStories"]["last_updated"] = today_str
        else:
            for i, card in enumerate(cards, 1):
                print(f"    Card {i}: {card.get('headline','?')}")
                print(f"      {card.get('body','')[:100]}...")
    except Exception as ex:
        print(f" ERROR: {ex}")

    # ── 3. Write ───────────────────────────────────────────────────────────
    if APPLY:
        DATA_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"\n  Written: {DATA_PATH}")
    else:
        print("\n  [Preview mode — no files written. Run with --apply to save.]")

    print("\nDone.")

if __name__ == "__main__":
    main()
