#!/usr/bin/env python3
"""
CB_update_stories.py — CARBONsnaps instrument story generator.

Detects instruments whose price has changed since the last story was written
(value_at_generation mismatch) and regenerates beginner/moderate/expert stories
via the Claude API.

Usage:
    python3 CB_update_stories.py            # preview: show stale instruments, no API calls
    python3 CB_update_stories.py --apply    # regenerate stories and write to CB_data.json

Exit codes:
    0 — clean (no mismatches found, or all resolved successfully)
    1 — one or more story generation attempts failed
"""

import json
import sys
import os
import argparse
from datetime import date
import anthropic
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

DATA_FILE = "CB_data.json"
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024

# Instruments with no price data — never touch these
PLACEHOLDER_PRICES = {"N/A", "--", "", None}

# One-time corrections applied in the same write pass as stories
FIELD_CORRECTIONS = {
    "EUA": {"price_unit": "GBP (CO2.L ETF proxy)"},
}

# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a carbon markets intelligence writer for CARBONsnaps, a B2B environmental commodity platform serving specialist funds, trading desks, and corporate carbon buyers.

Rules (non-negotiable):
- UK English spelling throughout (e.g. recognised, behaviour, licence).
- No em-dashes anywhere. Use commas, colons, parentheses, or restructure the sentence.
- Return only a JSON object with three keys: beginner, moderate, expert. No preamble, no markdown, no backticks.
- Do not include investment advice or specific buy/sell recommendations.
- Do not invent regulatory events not referenced in the input.

Story length and tone:
- beginner: 2-3 sentences. Plain language, no jargon. Explain what the instrument is and what the price move means in simple terms.
- moderate: 3-4 sentences. Adds mechanism and market context. Assumes reader knows what carbon markets are.
- expert: 4-5 sentences. Technical, positioning-aware. References regulatory backdrop, supply/demand dynamics, and forward implications where relevant.
"""

def build_user_prompt(inst: dict) -> str:
    spark = inst.get("spark", [])
    spark_summary = f"{len(spark)} data points" if spark else "no historical data"

    lines = [
        f"Instrument: {inst['name']} ({inst['id']})",
        f"Market family: {inst['market']}",
        f"Jurisdiction: {inst['jurisdiction']}",
        f"Current price: {inst['price']} {inst.get('price_unit', '')}",
        f"1-week change: {inst.get('change_1w', 'N/A')}",
        f"1-month change: {inst.get('change_1m', 'N/A')}",
        f"3-month change: {inst.get('change_3m', 'N/A')}",
        f"Regulatory signal: {inst.get('regulatory_signal', 'N/A')}",
        f"Regulatory note: {inst.get('regulatory_note', 'N/A')}",
        f"Price history: {spark_summary}",
        "",
        "Write instrument stories at three audience levels (beginner, moderate, expert).",
        "Return only a JSON object: {\"beginner\": \"...\", \"moderate\": \"...\", \"expert\": \"...\"}",
    ]
    return "\n".join(lines)

# ── Core logic ────────────────────────────────────────────────────────────────

def is_placeholder(price) -> bool:
    return price in PLACEHOLDER_PRICES

def is_stale(inst: dict) -> bool:
    price = inst.get("price")
    if is_placeholder(price):
        return False
    vag = inst.get("value_at_generation")
    return vag != price

def find_stale(instruments: list) -> list:
    return [i for i in instruments if is_stale(i)]

def generate_story(client: anthropic.Anthropic, inst: dict) -> dict:
    """Call Claude API and return parsed {beginner, moderate, expert} dict."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(inst)}],
    )
    raw = response.content[0].text.strip()
    # Strip accidental markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    stories = json.loads(raw)
    for key in ("beginner", "moderate", "expert"):
        if key not in stories:
            raise ValueError(f"Missing key '{key}' in API response for {inst['id']}")
    return stories

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CARBONsnaps instrument story updater")
    parser.add_argument("--apply", action="store_true", help="Write updated stories to CB_data.json")
    args = parser.parse_args()

    # Load data file
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: {DATA_FILE} not found. Run from the CARBONsnaps directory.")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    instruments = data.get("instruments", [])
    stale = find_stale(instruments)

    # ── Preview ────────────────────────────────────────────────────────────────

    if not stale:
        print("✓ All instruments clean — no VAG mismatches found.")
        sys.exit(0)

    print(f"{'PREVIEW' if not args.apply else 'APPLY'} — {len(stale)} instrument(s) need story refresh:\n")
    for inst in stale:
        vag = inst.get("value_at_generation", "absent")
        print(f"  {inst['id']:8s}  price={inst['price']}  value_at_generation={vag}")

    # Apply field corrections preview
    corrections_due = {
        iid: fields
        for iid, fields in FIELD_CORRECTIONS.items()
        if any(
            inst["id"] == iid and inst.get(k) != v
            for inst in instruments
            for k, v in fields.items()
        )
    }
    if corrections_due:
        print(f"\nField corrections to apply:")
        for iid, fields in corrections_due.items():
            for k, v in fields.items():
                orig = next((i.get(k) for i in instruments if i["id"] == iid), "?")
                print(f"  {iid}.{k}: '{orig}' → '{v}'")

    if not args.apply:
        print("\nDry run complete. Pass --apply to regenerate stories.")
        sys.exit(0)

    # ── Apply ──────────────────────────────────────────────────────────────────

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nERROR: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    today = date.today().isoformat()
    failed = []

    print()
    for inst in stale:
        iid = inst["id"]
        print(f"  [{iid}] Generating stories...", end=" ", flush=True)
        try:
            stories = generate_story(client, inst)

            # Write stories
            inst["story"] = {
                "beginner": stories["beginner"],
                "moderate": stories["moderate"],
                "expert": stories["expert"],
            }
            inst["value_at_generation"] = inst["price"]
            inst["last_updated"] = today

            # Apply any field corrections for this instrument
            for k, v in FIELD_CORRECTIONS.get(iid, {}).items():
                inst[k] = v

            print("done.")
            print(f"         beginner: {stories['beginner'][:80]}...")

        except (json.JSONDecodeError, ValueError, anthropic.APIError) as e:
            print(f"FAILED — {e}")
            failed.append(iid)

    # Write back (single atomic write)
    if len(failed) < len(stale):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        updated = len(stale) - len(failed)
        print(f"\n✓ {updated}/{len(stale)} instrument(s) updated. CB_data.json saved.")
    else:
        print("\nERROR: All story generation attempts failed. CB_data.json not modified.")

    if failed:
        print(f"  Failed instruments: {', '.join(failed)}")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
