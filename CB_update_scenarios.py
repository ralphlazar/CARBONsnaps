"""
CB_update_scenarios.py

Content-generation script. For each regulatory event in data.json where
display=true and scenarios is missing or empty, calls the Claude API
(Sonnet with web search) to generate a 3-scenario block.

Pipeline architecture rule: this script contacts the Claude API directly.
It is a content-generation script, not a sync script. It reads from and
writes to CB_data.json only.

Usage:
    python3 CB_update_scenarios.py              # preview — prints which events would be updated
    python3 CB_update_scenarios.py --apply      # writes scenarios to CB_data.json (missing only)
    python3 CB_update_scenarios.py --apply --force       # regenerates ALL events unconditionally
    python3 CB_update_scenarios.py --stale-only          # preview stale events (default 7-day window)
    python3 CB_update_scenarios.py --stale-only 14       # preview with 14-day staleness threshold
    python3 CB_update_scenarios.py --apply --stale-only  # regenerate only stale events (7-day default)
    python3 CB_update_scenarios.py --apply --stale-only 14   # regenerate stale events, 14-day window

Staleness rules (--stale-only mode):
    An event's scenarios are considered stale if ANY of the following:
    1. Scenarios are missing entirely.
    2. No generated_at timestamp is present (scenario-level or event-level fallback).
    3. generated_at is older than N days (N supplied as --stale-only argument, default 7).
    4. The event's direction, status, or note_version has changed since scenarios were
       last generated (detected via scenarios_content_snapshot). If note_version is absent
       from the data, that check is silently skipped.

Auth: Claude API key read from ANTHROPIC_API_KEY env var or .env file in script directory.
"""

import os
import re
import sys
import json
import time
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

import anthropic

# Load .env from script directory if present
_env_path = Path.home() / "Desktop" / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_JSON_PATH = Path(__file__).parent / "CB_data.json"
MODEL = "claude-sonnet-4-20250514"
DEFAULT_STALE_DAYS = 7

SCENARIO_SYSTEM = """\
You are a carbon-market regulatory analyst. You write concise, hedged scenario analyses for regulatory events.

Rules:
- Return ONLY valid JSON. No preamble, no explanation, no markdown fences.
- The response must be a single JSON object with a "scenarios" key containing exactly 3 objects.
- The three cases must be "base", "bull", "bear" in that order.
- Probabilities must be integers summing to exactly 100.
- Each rationale must be exactly one sentence, hedged language, UK English, no em-dashes.
- price_impact must contain a key for every instrument in instruments_affected.
- price_impact values are short strings such as "+5 to +10%", "neutral", "-10 to -15%", "modest upside", etc.
- Use the source label as context for confidence calibration.
- CRITICAL — direction alignment: the event has a direction field (Bullish / Bearish / Neutral / Mixed). Your scenario probabilities and price_impact values MUST be consistent with it. Bullish: base+bull probabilities combined must exceed bear by a clear margin, and base/bull price_impacts must show positive numbers. Bearish: bear probability must be the largest single case or bear+base combined clearly dominant, and bear price_impact must show negative numbers. Neutral: spread probabilities roughly evenly. Mixed: base dominates, bull and bear roughly equal. Do not contradict the stated direction.

Output schema:
{
  "scenarios": [
    {
      "case": "base",
      "probability": 55,
      "rationale": "One hedged sentence in UK English.",
      "price_impact": {"EUA": "+3 to +5%"}
    },
    {
      "case": "bull",
      "probability": 25,
      "rationale": "One hedged sentence in UK English.",
      "price_impact": {"EUA": "+8 to +12%"}
    },
    {
      "case": "bear",
      "probability": 20,
      "rationale": "One hedged sentence in UK English.",
      "price_impact": {"EUA": "-5 to -8%"}
    }
  ]
}
"""


def build_user_prompt(ev):
    instruments = ", ".join(ev.get("instruments_affected", []))
    lines = [
        f"Event ID: {ev['event_id']}",
        f"Title: {ev['title']}",
        f"Jurisdiction: {ev['jurisdiction']}",
        f"Instruments affected: {instruments}",
        f"Direction: {ev.get('direction', '')}",
        f"Confidence: {ev.get('confidence', 'not set')}",
        f"Magnitude: {ev.get('magnitude', 'not set')}",
        f"Status: {ev.get('status', '')}",
        f"Next date: {ev.get('next_date') or 'not set'}",
        f"Summary: {ev.get('summary', '')}",
    ]
    if ev.get("analyst_note"):
        lines.append(f"Analyst note: {ev['analyst_note']}")
    if ev.get("source_label"):
        lines.append(f"Source: {ev['source_label']}")
    lines.append("")
    lines.append(
        f"Generate a 3-scenario analysis (base, bull, bear) for this event. "
        f"price_impact must include keys for: {instruments}."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Staleness detection
# ---------------------------------------------------------------------------

def _resolve_generated_at(ev):
    """
    Return the generation timestamp for this event's scenarios, or None if absent.

    Lookup order:
      1. generated_at on the first scenario object  (new — written by this script)
      2. scenarios_at_generation on the event        (legacy — written by older versions)
    """
    scenarios = ev.get("scenarios")
    if scenarios and isinstance(scenarios, list) and len(scenarios) > 0:
        ts = scenarios[0].get("generated_at")
        if ts:
            return ts
    return ev.get("scenarios_at_generation")


def staleness_check(ev, max_age_days):
    """
    Determine whether an event's scenarios need regenerating.

    Returns
    -------
    (stale : bool, reason : str)
        reason is a human-readable string explaining the decision, suitable
        for console output.
    """
    scenarios = ev.get("scenarios")
    eid = ev.get("event_id", "?")

    # ── 1. Scenarios missing entirely ────────────────────────────────────────
    if not scenarios:
        return True, "scenarios missing"

    # ── 2. No timestamp — cannot confirm freshness ────────────────────────────
    generated_at_str = _resolve_generated_at(ev)
    if not generated_at_str:
        return True, "generated_at missing — cannot confirm freshness"

    # ── 3. Age check ──────────────────────────────────────────────────────────
    try:
        generated_at = datetime.fromisoformat(generated_at_str)
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - generated_at
        age_days = age.days
    except (ValueError, TypeError):
        return True, f"generated_at unparseable ({generated_at_str!r})"

    if age_days > max_age_days:
        return True, f"age {age_days}d exceeds threshold of {max_age_days}d"

    # ── 4. Content-change check ───────────────────────────────────────────────
    # Only performed when a content snapshot was previously recorded.
    # Events generated by older versions of this script have no snapshot; in
    # that case we rely solely on the age check above and skip content diffing.
    # The snapshot is written on every --apply run, so future runs will pick it up.
    snapshot = ev.get("scenarios_content_snapshot")
    if snapshot is not None:
        current_direction = ev.get("direction", "")
        current_status = ev.get("status", "")
        current_note_version = ev.get("note_version")  # may not exist yet

        if snapshot.get("direction") != current_direction:
            old = snapshot.get("direction", "<not recorded>")
            return True, f"direction changed  {old!r} → {current_direction!r}"

        if snapshot.get("status") != current_status:
            old = snapshot.get("status", "<not recorded>")
            return True, f"status changed  {old!r} → {current_status!r}"

        # note_version: only compare if BOTH the snapshot and the current event carry it.
        # If the column hasn't been added to the sheet yet, skip silently.
        if current_note_version is not None and "note_version" in snapshot:
            if snapshot["note_version"] != current_note_version:
                return True, (
                    f"note_version changed  {snapshot['note_version']} → {current_note_version}"
                )

    # ── Fresh ─────────────────────────────────────────────────────────────────
    age_str = f"{age_days}d" if age_days > 0 else f"{age.seconds // 3600}h"
    return False, f"fresh — {age_str} old, no content changes"


def build_content_snapshot(ev):
    """
    Return a dict capturing the event fields that drive staleness detection.
    Stored on the event at write time so future runs can diff against them.
    """
    snap = {
        "direction": ev.get("direction", ""),
        "status": ev.get("status", ""),
    }
    # Only persist note_version if the field is actually present on the event,
    # so that adding it later doesn't immediately mark everything stale.
    if ev.get("note_version") is not None:
        snap["note_version"] = ev["note_version"]
    return snap


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_scenarios(scenarios, instruments_affected):
    """Returns (ok: bool, error: str)."""
    if not isinstance(scenarios, list) or len(scenarios) != 3:
        return False, f"Expected list of 3 scenarios, got {type(scenarios).__name__} len={len(scenarios) if isinstance(scenarios, list) else '?'}"

    cases_found = {s.get("case") for s in scenarios}
    required_cases = {"base", "bull", "bear"}
    if cases_found != required_cases:
        return False, f"Expected cases base/bull/bear, got {cases_found}"

    total_prob = sum(s.get("probability", 0) for s in scenarios)
    if total_prob != 100:
        return False, f"Probabilities sum to {total_prob}, expected 100"

    for s in scenarios:
        pi = s.get("price_impact", {})
        missing = [i for i in instruments_affected if i not in pi]
        if missing:
            return False, f"Case '{s['case']}' missing price_impact keys: {missing}"
        if not isinstance(s.get("rationale"), str) or not s["rationale"].strip():
            return False, f"Case '{s['case']}' has empty rationale"

    return True, ""


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def generate_scenarios(client, ev, retries=2):
    """Call Claude API. Returns validated scenarios list or raises."""
    prompt = build_user_prompt(ev)

    for attempt in range(retries + 1):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SCENARIO_SYSTEM,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text blocks (web search may produce tool_use blocks too)
            text_content = ""
            for block in response.content:
                if block.type == "text":
                    text_content += block.text

            if not text_content.strip():
                raise ValueError("No text content in response")

            # Strip accidental markdown fences
            clean = text_content.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean.rsplit("```", 1)[0]
            clean = clean.strip()

            # Strip citation tags injected by web search tool
            clean = re.sub(r"</?cite[^>]*>", "", clean)

            parsed = json.loads(clean)
            scenarios = parsed.get("scenarios")
            if not scenarios:
                raise ValueError("JSON missing 'scenarios' key")

            instruments = ev.get("instruments_affected", [])
            ok, err = validate_scenarios(scenarios, instruments)
            if not ok:
                raise ValueError(f"Validation failed: {err}")

            return scenarios

        except Exception as exc:
            if attempt < retries:
                print(f"    [RETRY {attempt+1}] {ev['event_id']}: {exc}")
                time.sleep(2)
            else:
                raise


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(apply=False, force=False, stale_only=None):
    """
    Parameters
    ----------
    apply      : bool  — write changes to CB_data.json (False = preview only)
    force      : bool  — regenerate every event, bypassing all staleness checks
    stale_only : int | None
                 When set, only events that fail the staleness check are
                 processed.  The integer is the max-age threshold in days.
                 When None, the legacy behaviour applies: process events whose
                 scenarios are absent (or all events when force=True).
    """
    today_str = datetime.now(timezone.utc).isoformat()

    mode_label = "APPLY" if apply else "PREVIEW"
    filter_label = (
        f"--force (regenerate all)"
        if force
        else f"--stale-only {stale_only}d"
        if stale_only is not None
        else "missing scenarios only"
    )
    print(f"CB_update_scenarios.py — {mode_label} mode  [{filter_label}]")
    print(f"Timestamp: {today_str}")
    print()

    # ── Load data.json ────────────────────────────────────────────────────────
    if not DATA_JSON_PATH.exists():
        print(f"[FATAL] CB_data.json not found at {DATA_JSON_PATH}")
        sys.exit(1)

    with open(DATA_JSON_PATH) as f:
        data = json.load(f)

    events = data.get("regulatory", {}).get("events", [])
    if not events:
        print("No events found in data.regulatory.events. Nothing to do.")
        return

    # ── Triage events ─────────────────────────────────────────────────────────
    to_process = []   # list of (ev, reason_str)
    to_skip    = []   # list of (ev, reason_str)

    for ev in events:
        eid = ev["event_id"]

        if force:
            to_process.append((ev, "forced regeneration"))
            continue

        if stale_only is not None:
            # Staleness-aware filter
            stale, reason = staleness_check(ev, stale_only)
            if stale:
                to_process.append((ev, reason))
            else:
                to_skip.append((ev, reason))
        else:
            # Legacy behaviour: regenerate only if scenarios absent
            if ev.get("scenarios"):
                to_skip.append((ev, "scenarios already present"))
            else:
                to_process.append((ev, "scenarios missing"))

    # ── Summary header ────────────────────────────────────────────────────────
    print(f"Total events:      {len(events)}")
    print(f"To regenerate:     {len(to_process)}")
    print(f"To skip:           {len(to_skip)}")
    print()

    # ── Per-event skip report ─────────────────────────────────────────────────
    if to_skip:
        print("SKIPPING (no API call):")
        for ev, reason in to_skip:
            print(f"  ✓ {ev['event_id']:12s}  {reason}")
        print()

    # ── Per-event regenerate report ───────────────────────────────────────────
    if to_process:
        print(f"{'GENERATING' if apply else 'WOULD GENERATE'} (API call per event):")
        for ev, reason in to_process:
            instruments = ", ".join(ev.get("instruments_affected", []))
            print(f"  ✗ {ev['event_id']:12s}  {reason:<45s}  [{instruments}]")
        print()
    else:
        print("Nothing to regenerate.")
        if not force and stale_only is not None:
            print(f"All scenarios are fresh within the {stale_only}-day window.")
        elif not force:
            print("Use --force to regenerate existing scenarios.")
        return

    if not apply:
        print("Preview only — run with --apply to execute API calls and write.")
        return

    # ── Initialise API client ─────────────────────────────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[FATAL] ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Build lookup so we can update events in-place
    event_index = {ev["event_id"]: ev for ev in events}

    succeeded = []
    failed    = []

    print("─" * 60)

    for ev, reason in to_process:
        eid = ev["event_id"]
        instruments = ", ".join(ev.get("instruments_affected", []))
        print(f"  Generating: {eid} — {ev['title'][:50]}  [{instruments}]")
        print(f"    Reason: {reason}")
        try:
            scenarios = generate_scenarios(client, ev)

            # Stamp each scenario object with generated_at
            for scenario in scenarios:
                scenario["generated_at"] = today_str

            # Write back to event
            target = event_index[eid]
            target["scenarios"] = scenarios
            # Keep legacy event-level timestamp for any tooling that reads it
            target["scenarios_at_generation"] = today_str
            # Record content snapshot so future runs can detect drift
            target["scenarios_content_snapshot"] = build_content_snapshot(ev)

            succeeded.append(eid)
            probs = [s["probability"] for s in scenarios]
            print(f"    OK  probabilities: {probs}")

        except Exception as exc:
            failed.append(eid)
            print(f"    [FAIL] {eid}: {exc}")

        time.sleep(0.5)  # polite pause between calls

    print("─" * 60)
    print()
    print(f"Results: {len(succeeded)} succeeded, {len(failed)} failed")
    if failed:
        print(f"  Failed IDs: {', '.join(failed)}")

    # ── Write back ────────────────────────────────────────────────────────────
    with open(DATA_JSON_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nWritten to {DATA_JSON_PATH}")
    print("Done.")

    if failed:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate scenario blocks for regulatory events.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 CB_update_scenarios.py                    # preview missing scenarios
  python3 CB_update_scenarios.py --apply            # generate missing scenarios
  python3 CB_update_scenarios.py --apply --force    # regenerate everything
  python3 CB_update_scenarios.py --stale-only       # preview stale (7-day default)
  python3 CB_update_scenarios.py --stale-only 14    # preview stale (14-day window)
  python3 CB_update_scenarios.py --apply --stale-only      # regenerate stale (7d)
  python3 CB_update_scenarios.py --apply --stale-only 14   # regenerate stale (14d)
""",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write to CB_data.json (default is preview only)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate scenarios for ALL events, bypassing all staleness checks",
    )
    parser.add_argument(
        "--stale-only",
        nargs="?",
        const=DEFAULT_STALE_DAYS,
        type=int,
        metavar="N",
        dest="stale_only",
        help=(
            f"Regenerate only events whose scenarios are stale. "
            f"N = max age in days before a scenario is considered stale "
            f"(default: {DEFAULT_STALE_DAYS}). Also regenerates if direction, "
            f"status, or note_version has changed since last generation."
        ),
    )
    args = parser.parse_args()

    if args.force and args.stale_only is not None:
        print("Note: --force overrides --stale-only. All events will be regenerated.")
        print()

    run(apply=args.apply, force=args.force, stale_only=args.stale_only)
