"""
CB_diff.py

Compares the current CB_data.json regulatory events against the previous
build snapshot (last_state.json) and writes changelog.json.

Must be run BEFORE CB_sync_regulatory.py and CB_build.py in the full
refresh sequence:

    python3 CB_diff.py --apply
    python3 CB_sync_regulatory.py --apply
    python3 CB_update_scenarios.py --apply --stale-only
    python3 CB_build.py && open index.html

Usage:
    python3 CB_diff.py            # preview — prints diffs, writes nothing
    python3 CB_diff.py --apply    # writes changelog.json + last_state.json

On first run (no last_state.json):
    Creates the initial snapshot. changelog.json will be empty.
    No events are treated as "new" on first run to avoid a 30-entry flood.

Files:
    last_state.json   — snapshot of event fields from the previous build
    changelog.json    — diff output consumed by CB_build.py
"""

import json
import sys
import argparse
from datetime import date, datetime, timezone
from pathlib import Path

DATA_FILE      = Path("CB_data.json")
STATE_FILE     = Path("last_state.json")
CHANGELOG_FILE = Path("changelog.json")

TODAY = date.today().isoformat()
NOW   = datetime.now(timezone.utc).isoformat()

# Fields tracked for diff purposes
TRACKED_FIELDS = ["status", "next_date", "direction", "note_version"]

# Significance rules (evaluated in order; first match wins)
def significance(change_type, days_until=None):
    if change_type in ("status", "new_event"):
        return "high"
    if change_type == "date" and days_until is not None and days_until <= 60:
        return "high"
    if change_type == "note":
        return "medium"
    return "low"


def days_until(date_str):
    """Return days until next_date, or None if unparseable."""
    if not date_str:
        return None
    try:
        # Handle DD/MM/YYYY
        import re
        dmy = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', date_str)
        if dmy:
            d = date(int(dmy[3]), int(dmy[2]), int(dmy[1]))
            return (d - date.today()).days
        # Handle YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            d = date.fromisoformat(date_str)
            return (d - date.today()).days
        # Quarter / half / month: use start of period
        qm = re.match(r'^(\d{4})-Q([1-4])$', date_str)
        if qm:
            starts = [1, 4, 7, 10]
            d = date(int(qm[1]), starts[int(qm[2]) - 1], 1)
            return (d - date.today()).days
        hm = re.match(r'^(\d{4})-H([12])$', date_str)
        if hm:
            m = 1 if hm[2] == '1' else 7
            d = date(int(hm[1]), m, 1)
            return (d - date.today()).days
        mm = re.match(r'^(\d{4})-(\d{2})$', date_str)
        if mm:
            d = date(int(mm[1]), int(mm[2]), 1)
            return (d - date.today()).days
    except (ValueError, TypeError):
        pass
    return None


def snapshot_event(ev):
    """Extract only the fields we diff against."""
    snap = {"event_id": ev.get("event_id"), "title": ev.get("title", "")}
    for f in TRACKED_FIELDS:
        snap[f] = ev.get(f)
    return snap


def diff_events(old_map, new_map, first_run):
    """
    Returns a list of change dicts.

    old_map / new_map: {event_id: snapshot_dict}
    first_run: if True, no "new_event" entries are emitted (avoids a 30-entry flood).
    """
    changes = []

    # New events
    if not first_run:
        for eid, new_ev in new_map.items():
            if eid not in old_map:
                du = days_until(new_ev.get("next_date"))
                changes.append({
                    "id":           eid,
                    "title":        new_ev.get("title", ""),
                    "change_type":  "new_event",
                    "from":         None,
                    "to":           None,
                    "week":         TODAY,
                    "significance": significance("new_event", du),
                    "note":         "New event added to the tracker.",
                })

    # Changed fields on existing events
    for eid, new_ev in new_map.items():
        if eid not in old_map:
            continue
        old_ev = old_map[eid]

        if old_ev.get("status") != new_ev.get("status"):
            du = days_until(new_ev.get("next_date"))
            changes.append({
                "id":           eid,
                "title":        new_ev.get("title", ""),
                "change_type":  "status",
                "from":         old_ev.get("status"),
                "to":           new_ev.get("status"),
                "week":         TODAY,
                "significance": significance("status"),
                "note":         "",
            })

        if old_ev.get("next_date") != new_ev.get("next_date"):
            du = days_until(new_ev.get("next_date"))
            changes.append({
                "id":           eid,
                "title":        new_ev.get("title", ""),
                "change_type":  "date",
                "from":         old_ev.get("next_date"),
                "to":           new_ev.get("next_date"),
                "week":         TODAY,
                "significance": significance("date", du),
                "note":         "",
            })

        if old_ev.get("direction") != new_ev.get("direction"):
            changes.append({
                "id":           eid,
                "title":        new_ev.get("title", ""),
                "change_type":  "direction",
                "from":         old_ev.get("direction"),
                "to":           new_ev.get("direction"),
                "week":         TODAY,
                "significance": significance("direction"),
                "note":         "",
            })

        old_nv = old_ev.get("note_version")
        new_nv = new_ev.get("note_version")
        if old_nv is not None and new_nv is not None and old_nv != new_nv:
            changes.append({
                "id":           eid,
                "title":        new_ev.get("title", ""),
                "change_type":  "note",
                "from":         str(old_nv),
                "to":           str(new_nv),
                "week":         TODAY,
                "significance": significance("note"),
                "note":         "Analyst note updated.",
            })

    return changes


def run(apply=False):
    # ── Load CB_data.json ──────────────────────────────────────────────────────
    if not DATA_FILE.exists():
        print(f"[FATAL] {DATA_FILE} not found.")
        sys.exit(1)

    with open(DATA_FILE) as f:
        data = json.load(f)

    events = data.get("regulatory", {}).get("events", [])
    new_map = {ev["event_id"]: snapshot_event(ev) for ev in events if "event_id" in ev}

    # ── Load last_state.json (or treat as first run) ───────────────────────────
    first_run = False
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
        old_map = {s["event_id"]: s for s in state.get("events", []) if "event_id" in s}
    else:
        print("No last_state.json found. This is the first run.")
        print("Initial snapshot will be written. changelog.json will be empty.")
        old_map = {}
        first_run = True

    # ── Diff ──────────────────────────────────────────────────────────────────
    changes = diff_events(old_map, new_map, first_run)

    # ── Report ────────────────────────────────────────────────────────────────
    mode = "APPLY" if apply else "PREVIEW"
    print(f"\nCB_diff.py — {mode} mode   {TODAY}")
    print(f"  Events in current data : {len(new_map)}")
    print(f"  Events in last snapshot: {len(old_map)}")
    print(f"  Changes detected       : {len(changes)}")
    print()

    if changes:
        high = [c for c in changes if c["significance"] == "high"]
        med  = [c for c in changes if c["significance"] == "medium"]
        low  = [c for c in changes if c["significance"] == "low"]
        print(f"  High  : {len(high)}")
        print(f"  Medium: {len(med)}")
        print(f"  Low   : {len(low)}")
        print()
        for c in changes:
            sig_label = {"high": "HIGH", "medium": "MED ", "low": "LOW "}.get(c["significance"], "    ")
            frm = f"  {c['from']} -> {c['to']}" if c["from"] is not None else ""
            print(f"  [{sig_label}] {c['id']:12s}  {c['change_type']:10s}  {c['title'][:45]}{frm}")
    else:
        print("  No changes detected.")

    if not apply:
        print("\nPreview only — run with --apply to write changelog.json and last_state.json.")
        return

    # ── Write changelog.json ──────────────────────────────────────────────────
    # Load existing changelog and prepend new changes (keep last 8 weeks)
    existing = []
    if CHANGELOG_FILE.exists():
        with open(CHANGELOG_FILE) as f:
            existing = json.load(f).get("changes", [])

    # Remove entries older than 8 weeks from today
    from datetime import timedelta
    cutoff = (date.today() - timedelta(weeks=8)).isoformat()
    existing = [c for c in existing if c.get("week", "0000-00-00") >= cutoff]

    # Prepend today's changes (newest first)
    all_changes = changes + existing

    changelog = {
        "generated":  TODAY,
        "generated_at": NOW,
        "changes":    all_changes,
    }
    with open(CHANGELOG_FILE, "w") as f:
        json.dump(changelog, f, indent=2, ensure_ascii=False)
    print(f"\n  Written: {CHANGELOG_FILE}  ({len(all_changes)} total entries, {len(changes)} new)")

    # ── Write last_state.json ─────────────────────────────────────────────────
    state_out = {
        "generated":  TODAY,
        "generated_at": NOW,
        "events":     list(new_map.values()),
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state_out, f, indent=2, ensure_ascii=False)
    print(f"  Written: {STATE_FILE}  ({len(new_map)} events snapshotted)")
    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diff regulatory events and write changelog.")
    parser.add_argument("--apply", action="store_true", help="Write changelog.json and last_state.json")
    args = parser.parse_args()
    run(apply=args.apply)
