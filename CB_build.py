#!/usr/bin/env python3
"""
CARBONsnaps build.py
====================
Validates data.json, detects changes vs yesterday's backup,
merges shell + data -> final index.html, and stamps today's date.

Usage:
    python3 build.py

Requires: CB_data.json and CB_carbonsnaps-shell.html in the same folder.
Output:   index.html (ready to publish)
"""

import json
import sys
import os
import re
import shutil
import subprocess
from datetime import date, datetime

# ── Config ───────────────────────────────────────────────────────────────────
SHELL_FILE  = "CB_carbonsnaps-shell.html"
DATA_FILE   = "CB_data.json"
OUTPUT_FILE = "index.html"
BACKUP_DIR      = "backups"
CHANGELOG_FILE  = "changelog.json"
TODAY           = date.today().isoformat()
NOW             = datetime.now().strftime("%Y-%m-%d %H:%M")

# Expected instrument IDs
EXPECTED_INSTRUMENTS = {
    "EUA", "CCA", "UKA", "CORSIA", "LCFS", "RIN", "45Z", "VCM"
}

# Required fields on every instrument
INSTRUMENT_REQUIRED_FIELDS = [
    "id", "name", "short", "market", "jurisdiction",
    "price", "price_unit", "regulatory_signal",
    "last_updated", "story"
]

# Valid regulatory signal values (direction system)
VALID_SIGNALS = {"Bullish", "Bearish", "Mixed", "Neutral"}

# Valid market categories
VALID_MARKETS = {"Compliance", "Clean Fuel", "Voluntary"}

STORY_LEVELS = ["expert"]

# ── Helpers ───────────────────────────────────────────────────────────────────
errors   = []
warnings = []

def err(msg):  errors.append(f"  x {msg}")
def warn(msg): warnings.append(f"  !  {msg}")
def ok(msg):   print(f"  + {msg}")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Load and parse
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  CARBONsnaps Build Script")
print(f"  {NOW}")
print("="*60)

for fname in [SHELL_FILE, DATA_FILE]:
    if not os.path.exists(fname):
        print(f"\n  FATAL: '{fname}' not found in current directory.\n")
        sys.exit(1)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    raw = f.read()

try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"\n  FATAL: data.json is not valid JSON.\n  Error: {e}\n")
    sys.exit(1)

ok("data.json parsed as valid JSON")

# ── Ingest changelog.json if present ─────────────────────────────────────────
print("\n-- Changelog ----------------------------------------------------")
if os.path.exists(CHANGELOG_FILE):
    with open(CHANGELOG_FILE) as f:
        changelog = json.load(f)
    data.setdefault("regulatory", {})["changelog"] = changelog
    n = len(changelog.get("changes", []))
    high = sum(1 for c in changelog.get("changes", []) if c.get("significance") == "high")
    ok(f"changelog.json ingested — {n} entries, {high} high-significance")
else:
    data.setdefault("regulatory", {})["changelog"] = {"generated": TODAY, "changes": []}
    print("  No changelog.json found — empty changelog injected. Run CB_diff.py --apply first.")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Schema validation
# ════════════════════════════════════════════════════════════════════════════
print("\n-- Validating schema ----------------------------------------")

# Top-level keys
required_top = {"_meta", "instruments", "regulatory", "globalStories"}
missing_top = required_top - set(data.keys())
if missing_top:
    for k in missing_top:
        err(f"Top-level key missing: '{k}'")
else:
    ok("Top-level keys present")

# _meta
meta = data.get("_meta", {})
if "generated" not in meta:
    err("_meta.generated is missing")
else:
    ok(f"_meta.generated = {meta['generated']}")

# ── Instruments ──────────────────────────────────────────────────────────────
instruments = data.get("instruments", [])
if not isinstance(instruments, list):
    err("instruments must be a list")
    instruments = []

found_ids = {i.get("id") for i in instruments if isinstance(i, dict)}
missing_ids = EXPECTED_INSTRUMENTS - found_ids
extra_ids   = found_ids - EXPECTED_INSTRUMENTS

if missing_ids:
    err(f"Missing instrument IDs: {sorted(missing_ids)}")
else:
    ok(f"All {len(EXPECTED_INSTRUMENTS)} instruments present")

if extra_ids:
    warn(f"Unexpected instrument IDs: {sorted(extra_ids)}")

for instrument in instruments:
    if not isinstance(instrument, dict):
        err("instrument entry is not a dict")
        continue

    iid = instrument.get("id", "UNKNOWN")

    # Required fields
    for field in INSTRUMENT_REQUIRED_FIELDS:
        if field not in instrument:
            err(f"[{iid}] missing required field '{field}'")

    # Regulatory signal
    signal = instrument.get("regulatory_signal")
    if signal and signal not in VALID_SIGNALS:
        err(f"[{iid}] regulatory_signal must be one of {VALID_SIGNALS}, got '{signal}'")

    # Market category
    market = instrument.get("market")
    if market and market not in VALID_MARKETS:
        err(f"[{iid}] market must be one of {VALID_MARKETS}, got '{market}'")

    # Story tiers
    story = instrument.get("story", {})
    if not isinstance(story, dict):
        err(f"[{iid}] story must be a dict with beginner/moderate/expert keys")
    else:
        for level in STORY_LEVELS:
            if level not in story or not story[level]:
                err(f"[{iid}] story.{level} missing or empty")

    # value_at_generation mismatch guard
    vag = instrument.get("value_at_generation")
    current_price = str(instrument.get("price", "")).strip()
    if vag is not None and str(vag).strip() != current_price:
        err(
            f"[{iid}] story mismatch: written for '{vag}', "
            f"current price is '{current_price}'. "
            f"Re-run update_stories.py for this instrument."
        )

    # Spark array (warn if empty, not error — expected during build-out)
    spark = instrument.get("spark", [])
    if not isinstance(spark, list):
        err(f"[{iid}] spark must be a list")
    elif len(spark) == 0:
        warn(f"[{iid}] spark array is empty (populate once price history source is wired up)")
    elif len(spark) < 12:
        warn(f"[{iid}] spark array has only {len(spark)} points (expected 12+)")

# ── Regulatory block ──────────────────────────────────────────────────────────
regulatory = data.get("regulatory", {})
if not isinstance(regulatory, dict):
    err("regulatory must be a dict")
else:
    if "events" not in regulatory:
        err("regulatory.events missing")
    elif not isinstance(regulatory["events"], list):
        err("regulatory.events must be a list")

    stale = regulatory.get("stale_warnings", [])
    if stale:
        for sid in stale:
            warn(f"Regulatory tracker: stale event '{sid}' not reviewed in 30+ days")

# ── Global stories ─────────────────────────────────────────────────────────────
global_stories = data.get("globalStories", {})
if not isinstance(global_stories, dict):
    err("globalStories must be a dict")
else:
    cards = global_stories.get("cards", [])
    if not isinstance(cards, list):
        err("globalStories.cards must be a list")
    elif len(cards) == 0:
        err("globalStories.cards is empty — 3 story cards required")
    elif len(cards) < 3:
        warn(f"globalStories.cards has {len(cards)} card(s), expected 3")
    else:
        for i, card in enumerate(cards):
            if not isinstance(card, dict):
                err(f"globalStories.cards[{i}] must be a dict")
            else:
                for field in ["icon", "label", "headline", "body", "source"]:
                    if field not in card:
                        err(f"globalStories.cards[{i}] missing '{field}'")

if not errors:
    ok("Schema validation passed")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Change detection vs yesterday's backup
# ════════════════════════════════════════════════════════════════════════════
print("\n-- Change detection -----------------------------------------")

changed_prices  = []
changed_signals = []
changed_stories = []

yesterday_file = None
if os.path.isdir(BACKUP_DIR):
    backups = sorted([
        f for f in os.listdir(BACKUP_DIR)
        if f.startswith("data_") and f.endswith(".json")
    ], reverse=True)
    if backups:
        yesterday_file = os.path.join(BACKUP_DIR, backups[0])

if yesterday_file and os.path.exists(yesterday_file):
    print(f"  Comparing against backup: {yesterday_file}")
    with open(yesterday_file) as f:
        old = json.load(f)

    old_instruments = {
        i["id"]: i for i in old.get("instruments", [])
        if isinstance(i, dict) and "id" in i
    }
    new_instruments = {
        i["id"]: i for i in data.get("instruments", [])
        if isinstance(i, dict) and "id" in i
    }

    for iid, new_item in new_instruments.items():
        old_item = old_instruments.get(iid, {})

        # Price changes
        if str(new_item.get("price")) != str(old_item.get("price")):
            changed_prices.append(
                f"{iid}: {old_item.get('price')} -> {new_item.get('price')}"
            )

        # Regulatory signal changes
        if new_item.get("regulatory_signal") != old_item.get("regulatory_signal"):
            changed_signals.append(
                f"{iid}: {old_item.get('regulatory_signal')} -> {new_item.get('regulatory_signal')}"
            )

        # Story changes
        for level in STORY_LEVELS:
            new_story = new_item.get("story", {}).get(level, "")
            old_story = old_item.get("story", {}).get(level, "")
            if new_story != old_story:
                changed_stories.append(f"{iid}.story.{level}")

    print(f"  Price changes    : {len(changed_prices)}")
    print(f"  Signal changes   : {len(changed_signals)}")
    print(f"  Story changes    : {len(changed_stories)}")

    if changed_prices:
        print("\n  Price changes:")
        for c in changed_prices:
            print(f"    {c}")

    if changed_signals:
        print("\n  Signal changes:")
        for c in changed_signals:
            print(f"    {c}")

    if changed_stories:
        print("\n  Story changes:")
        for c in changed_stories:
            print(f"    {c}")

    if not changed_prices and not changed_signals and not changed_stories:
        warn("No changes detected vs yesterday. Is data.json up to date?")
else:
    print("  No backup found — skipping change detection.")
    print("  (First run, or backup folder is empty.)")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Abort if validation errors
# ════════════════════════════════════════════════════════════════════════════
if errors:
    print("\n-- Validation FAILED ----------------------------------------")
    for e in errors:
        print(e)
    if warnings:
        print("\n  Warnings:")
        for w in warnings:
            print(w)
    print(f"\n  BUILD ABORTED — fix the {len(errors)} error(s) above, then re-run.\n")
    sys.exit(1)

if warnings:
    print("\n-- Warnings -------------------------------------------------")
    for w in warnings:
        print(w)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Merge shell + data -> output
# ════════════════════════════════════════════════════════════════════════════
print("\n-- Building output ------------------------------------------")

with open(SHELL_FILE, "r", encoding="utf-8") as f:
    shell = f.read()

# Stamp title
shell = re.sub(
    r'<title>.*?</title>',
    f'<title>CARBONsnaps — Environmental Commodity Intelligence — {TODAY}</title>',
    shell
)

# Inline data.json as a standalone script block
data_json_str = json.dumps(data, ensure_ascii=False)

FETCH_OLD = (
    "fetch('data.json')\n"
    "  .then(r => { if(!r.ok) throw new Error('data.json not found: ' + r.status); return r.json(); })\n"
    "  .then(data => {"
)
FETCH_NEW = (
    "// data.json inlined by build.py — standalone file, no server needed\n"
    "Promise.resolve(window.__CARBONSNAPS_DATA__)\n"
    "  .then(data => {"
)

if FETCH_OLD not in shell:
    warn("Could not find fetch block to replace — output may require a server.")
else:
    shell = shell.replace(FETCH_OLD, FETCH_NEW)
    ok("Inlined data.json into HTML (standalone mode)")

# Inject data payload before </head>
inline_script = (
    f"\n<script>\n"
    f"// Inlined by build.py on {NOW}\n"
    f"window.__CARBONSNAPS_DATA__ = {data_json_str};\n"
    f"</script>\n"
)
shell = shell.replace("</head>", inline_script + "</head>", 1)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(shell)

ok(f"Written: {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE) // 1024} KB)")

# Stamp _meta in data.json
data["_meta"]["generated"] = TODAY
data["_meta"]["built_at"] = NOW
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
ok(f"Stamped _meta.generated = {TODAY} in data.json")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Backup
# ════════════════════════════════════════════════════════════════════════════
os.makedirs(BACKUP_DIR, exist_ok=True)
backup_path = os.path.join(BACKUP_DIR, f"data_{TODAY}.json")
shutil.copy2(DATA_FILE, backup_path)
ok(f"Backup saved: {backup_path}")

all_backups = sorted([
    f for f in os.listdir(BACKUP_DIR)
    if f.startswith("data_") and f.endswith(".json")
])
if len(all_backups) > 30:
    for old_b in all_backups[:-30]:
        os.remove(os.path.join(BACKUP_DIR, old_b))
    ok(f"Pruned {len(all_backups) - 30} old backup(s), keeping 30 days")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Summary
# ════════════════════════════════════════════════════════════════════════════
print("\n-- Summary --------------------------------------------------")
print(f"  Date stamped     : {TODAY}")
print(f"  Instruments      : {len(instruments)}/{len(EXPECTED_INSTRUMENTS)}")
print(f"  Regulatory events: {len(data.get('regulatory', {}).get('events', []))}")
print(f"  Changelog entries: {len(data.get('regulatory', {}).get('changelog', {}).get('changes', []))}")
print(f"  Price changes    : {len(changed_prices)}")
print(f"  Signal changes   : {len(changed_signals)}")
print(f"  Story changes    : {len(changed_stories)}")
print(f"  Output           : {OUTPUT_FILE}")
print(f"  Backup           : {backup_path}")
print(f"\n  BUILD SUCCESSFUL — {OUTPUT_FILE} is ready to publish.\n")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Auto git commit
# ════════════════════════════════════════════════════════════════════════════
commit_msg = f"Build {TODAY} — auto commit"
result = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
if result.returncode != 0:
    print(f"  ! git add failed: {result.stderr.strip()}")
else:
    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            print("  git: nothing to commit, working tree clean")
        else:
            print(f"  ! git commit failed: {result.stderr.strip()}")
    else:
        print(f"  + git commit: {commit_msg}")
        result = subprocess.run(
            ["git", "push", "origin", "master"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ! git push failed: {result.stderr.strip()}")
        else:
            print("  + git push: origin master")
