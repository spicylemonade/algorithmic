#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def recompute_summary(data):
    counts = {"completed": 0, "in_progress": 0, "failed": 0, "pending": 0}
    for phase in data.get("phases", []):
        for item in phase.get("items", []):
            status = item.get("status", "pending")
            if status not in counts:
                counts["pending"] += 1
            else:
                counts[status] += 1
    data["summary"] = {
        "total_items": sum(counts.values()),
        "completed": counts["completed"],
        "in_progress": counts["in_progress"],
        "failed": counts["failed"],
        "pending": counts["pending"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rubric", default="research_rubric.json")
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--status", required=True, choices=["pending", "in_progress", "completed", "failed"])
    parser.add_argument("--notes", default=None)
    parser.add_argument("--error", default=None)
    args = parser.parse_args()

    path = Path(args.rubric)
    data = json.loads(path.read_text())

    found = None
    for phase in data.get("phases", []):
        for item in phase.get("items", []):
            if item.get("id") == args.item_id:
                found = item
                break
        if found:
            break

    if not found:
        raise SystemExit(f"Item not found: {args.item_id}")

    found["status"] = args.status
    if args.notes is not None:
        found["notes"] = args.notes
    if args.error is not None:
        found["error"] = args.error
    if args.status != "failed" and args.error is None:
        found["error"] = None

    recompute_summary(data)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
