#!/usr/bin/env python3
"""
CB_update_headlines.py — CARBONsnaps weekly global briefing generator.

Writes the three-act globalStories cards (beginner / moderate / expert) to
CB_data.json using the Claude API. Synthesises current instrument prices,
change fields, regulatory signals, and regulatory events into three cards:

  Card 1: This Week's Signal   — dominant regulatory or price move
  Card 2: Where It's Showing Up — which instruments are moving and how
  Card 3: What It Means         — positioning implication (not investment advice)

Usage:
    python3 CB_update_headlines.py            # preview: show inputs, no API calls
    python3 CB_update_headlines.py --apply    # generate and write to CB_data.json

Exit codes:
    0 — written successfully
    1 — generation failed
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
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2048

# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a carbon markets intelligence writer for CARBONsnaps, a B2B environmental commodity platform serving specialist funds, trading desks, and corporate carbon buyers.

You write the weekly global briefing: three cards that tell a coherent story across the carbon markets landscape.

Card structure (always exactly three cards):
  Card 1 — This Week's Signal: the dominant regulatory or price development this week.
  Card 2 — Where It's Showing Up: which instruments are moving and what the price action looks like.
  Card 3 — What It Means: the forward implication for positioning (not investment advice).

Each card has four fields:
  icon:   one of "sunny", "cloudy", or "stormy" — your editorial judgement on sentiment
  label:  a short headline (5-8 words)
  body:   the narrative (see length guidance below)
  source: a short attribution string, e.g. "CARB auction data" or "EU ETS price feed"

Rules (non-negotiable):
- UK English spelling throughout (e.g. recognised, behaviour, licence).
- No em-dashes anywhere. Use commas, colons, parentheses, or restructure the sentence.
- No investment advice or specific buy/sell recommendations.
- Do not invent regulatory events not present in the input.
- Return only a JSON object with three keys: beginner, moderate, expert.
  Each value is an array of exactly 3 card objects: [{icon, label, body, source}, ...]
- No preamble, no markdown, no backticks.

Body length and tone by audience:
  beginner:  2-3 sentences per card. Plain language, no jargon. Explain what is happening and why it matters in simple terms.
  moderate:  3-4 sentences per card. Adds mechanism and market context. Assumes reader knows what carbon markets are.
  expert:    4-5 sentences per card. Technical, positioning-aware. References supply/demand dynamics, regulatory calendar, and cross-instrument implications where relevant.
"""

def build_user_prompt(data: dict) -> str:
    instruments = data.get("instruments", [])
    regulatory = data.get("regulatory", {})
    events = regulatory.get("events", [])

    lines = ["=== INSTRUMENT SNAPSHOT ==="]
    for inst in instruments:
        price = inst.get("price", "N/A")
        if price in {"N/A", "--", "", None}:
            continue
        lines.append(
            f"{inst['id']} ({inst['name']}): "
            f"price={price} {inst.get('price_unit', '')}, "
            f"1w={inst.get('change_1w', 'N/A')}, "
            f"1m={inst.get('change_1m', 'N/A')}, "
            f"3m={inst.get('change_3m', 'N/A')}, "
            f"signal={inst.get('regulatory_signal', 'N/A')}, "
            f"note={inst.get('regulatory_note', 'N/A')}"
        )

    lines += ["", "=== REGULATORY EVENTS (active / upcoming) ==="]
    active_events = [
        e for e in events
        if e.get("status") in ("Active", "Upcoming")
    ]
    if active_events:
        for e in active_events[:10]:  # cap at 10 to manage context
            lines.append(
                f"[{e.get('event_type', '')}] {e.get('title', '')} "
                f"({e.get('jurisdiction', '')}, {e.get('status', '')}): "
                f"{e.get('summary', '')} "
                f"Direction={e.get('direction', 'N/A')}, "
                f"Magnitude={e.get('magnitude', 'N/A')}"
            )
    else:
        lines.append("No active or upcoming regulatory events.")

    lines += [
        "",
        "Write the weekly global briefing as three cards at each of three audience levels.",
        'Return only a JSON object: {"beginner": [{...}, {...}, {...}], "moderate": [...], "expert": [...]}',
        "Each card object must have exactly these keys: icon, label, body, source.",
        'icon must be one of: "sunny", "cloudy", "stormy".',
    ]
    return "\n".join(lines)

# ── Generation ────────────────────────────────────────────────────────────────

def generate_headlines(client: anthropic.Anthropic, data: dict) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(data)}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    result = json.loads(raw)

    # Validate structure
    for tier in ("beginner", "moderate", "expert"):
        if tier not in result:
            raise ValueError(f"Missing tier '{tier}' in API response")
        cards = result[tier]
        if not isinstance(cards, list) or len(cards) != 3:
            raise ValueError(f"Tier '{tier}' must have exactly 3 cards, got {len(cards)}")
        for i, card in enumerate(cards):
            for field in ("icon", "label", "body", "source"):
                if field not in card:
                    raise ValueError(f"Card {i+1} in '{tier}' missing field '{field}'")
            if card["icon"] not in ("sunny", "cloudy", "stormy"):
                raise ValueError(f"Card {i+1} in '{tier}' has invalid icon '{card['icon']}'")

    return result

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CARBONsnaps weekly briefing generator")
    parser.add_argument("--apply", action="store_true", help="Write generated briefing to CB_data.json")
    args = parser.parse_args()

    if not os.path.exists(DATA_FILE):
        print(f"ERROR: {DATA_FILE} not found. Run from the CARBONsnaps directory.")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ── Preview ────────────────────────────────────────────────────────────────

    print(f"{'PREVIEW' if not args.apply else 'APPLY'} — weekly global briefing generator\n")

    instruments_with_data = [
        i for i in data.get("instruments", [])
        if i.get("price") not in {"N/A", "--", "", None}
    ]
    events = data.get("regulatory", {}).get("events", [])
    active_events = [e for e in events if e.get("status") in ("Active", "Upcoming")]

    print(f"  Instruments with price data: {len(instruments_with_data)}")
    for inst in instruments_with_data:
        print(f"    {inst['id']:8s} {inst['price']} {inst.get('price_unit', '')}  1w={inst.get('change_1w', 'N/A')}")
    print(f"  Active/upcoming regulatory events: {len(active_events)}")

    if not args.apply:
        print("\nDry run complete. Pass --apply to generate briefing.")
        sys.exit(0)

    # ── Apply ──────────────────────────────────────────────────────────────────

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nERROR: ANTHROPIC_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("\n  Generating briefing (3 tiers, 3 cards each)...", end=" ", flush=True)
    try:
        global_stories = generate_headlines(client, data)
    except (json.JSONDecodeError, ValueError, anthropic.APIError) as e:
        print(f"FAILED\n\nERROR: {e}")
        sys.exit(1)

    print("done.")

    # Write back
    data["globalStories"] = {
        "beginner": global_stories["beginner"],
        "moderate": global_stories["moderate"],
        "expert": global_stories["expert"],
        "last_updated": date.today().isoformat(),
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ globalStories written to {DATA_FILE}.")
    print("\n  Preview (expert, Card 1):")
    card = global_stories["expert"][0]
    print(f"    [{card['icon']}] {card['label']}")
    print(f"    {card['body'][:120]}...")

    sys.exit(0)

if __name__ == "__main__":
    main()
