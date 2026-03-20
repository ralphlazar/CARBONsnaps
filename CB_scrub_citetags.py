"""
CB_scrub_citetags.py
One-off script. Strips <cite ...> and </cite> tags from all scenario
rationale fields already stored in CB_data.json.
Safe to run multiple times (idempotent).
"""
import json, re
from pathlib import Path

DATA_FILE = Path("CB_data.json")

with open(DATA_FILE) as f:
    data = json.load(f)

count = 0
for ev in data.get("regulatory", {}).get("events", []):
    for scenario in ev.get("scenarios", []):
        raw = scenario.get("rationale", "")
        clean = re.sub(r"</?cite[^>]*>", "", raw).strip()
        # Also replace em-dashes while we're here
        clean = clean.replace("\u2014", ", ").replace("\u2013", "-")
        if clean != raw:
            scenario["rationale"] = clean
            count += 1

with open(DATA_FILE, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Done. {count} rationale(s) cleaned.")
