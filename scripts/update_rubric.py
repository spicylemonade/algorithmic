#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path
import argparse


def recompute_summary(r):
    counts = {"completed": 0, "in_progress": 0, "failed": 0, "pending": 0}
    total = 0
    for ph in r.get("phases", []):
        for item in ph.get("items", []):
            total += 1
            st = item.get("status", "pending")
            if st not in counts:
                counts["pending"] += 1
            else:
                counts[st] += 1
    r["summary"] = {
        "total_items": total,
        "completed": counts["completed"],
        "in_progress": counts["in_progress"],
        "failed": counts["failed"],
        "pending": counts["pending"],
    }


def set_item_status(r, item_id, status, notes=None, error=None):
    found = False
    for ph in r.get("phases", []):
        for item in ph.get("items", []):
            if item.get("id") == item_id:
                item["status"] = status
                if notes is not None:
                    item["notes"] = notes
                if error is not None:
                    item["error"] = error
                found = True
    if not found:
        raise SystemExit(f"Item {item_id} not found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", default="research_rubric.json")
    ap.add_argument("--item", required=True)
    ap.add_argument("--status", required=True, choices=["pending", "in_progress", "completed", "failed"])
    ap.add_argument("--notes", default=None)
    ap.add_argument("--error", default=None)
    args = ap.parse_args()

    p = Path(args.rubric)
    r = json.loads(p.read_text())
    set_item_status(r, args.item, args.status, args.notes, args.error)
    r["updated_at"] = datetime.now(timezone.utc).isoformat()
    recompute_summary(r)
    p.write_text(json.dumps(r, indent=2) + "\n")


if __name__ == "__main__":
    main()
