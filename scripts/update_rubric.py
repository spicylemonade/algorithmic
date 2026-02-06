#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def recalc_summary(data: dict) -> None:
    counts = {"completed": 0, "in_progress": 0, "failed": 0, "pending": 0}
    total = 0
    for phase in data["phases"]:
        for item in phase["items"]:
            total += 1
            st = item["status"]
            counts[st] = counts.get(st, 0) + 1
    data["summary"] = {
        "total_items": total,
        "completed": counts.get("completed", 0),
        "in_progress": counts.get("in_progress", 0),
        "failed": counts.get("failed", 0),
        "pending": counts.get("pending", 0),
    }
    data["updated_at"] = now_iso()


def set_item(data: dict, item_id: str, status: str, notes: str | None, error: str | None) -> None:
    found = False
    for phase in data["phases"]:
        for item in phase["items"]:
            if item["id"] == item_id:
                item["status"] = status
                if status == "in_progress":
                    item["notes"] = None
                    item["error"] = None
                elif status == "completed":
                    item["notes"] = notes
                    item["error"] = None
                elif status == "failed":
                    item["notes"] = notes
                    item["error"] = error or "Unknown error"
                found = True
                break
        if found:
            break
    if not found:
        raise SystemExit(f"Item not found: {item_id}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("item_id")
    p.add_argument("status", choices=["in_progress", "completed", "failed"])
    p.add_argument("--notes", default=None)
    p.add_argument("--error", default=None)
    p.add_argument("--path", default="research_rubric.json")
    args = p.parse_args()

    path = Path(args.path)
    data = json.loads(path.read_text())
    set_item(data, args.item_id, args.status, args.notes, args.error)
    recalc_summary(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
