#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def recompute_summary(data: dict) -> None:
    counts = {"completed": 0, "in_progress": 0, "failed": 0, "pending": 0}
    for phase in data["phases"]:
        for item in phase["items"]:
            status = item["status"]
            counts[status] = counts.get(status, 0) + 1
    data["summary"] = {
        "total_items": sum(counts.values()),
        "completed": counts.get("completed", 0),
        "in_progress": counts.get("in_progress", 0),
        "failed": counts.get("failed", 0),
        "pending": counts.get("pending", 0),
    }


def set_item(data: dict, item_id: str, status: str, notes: str | None, error: str | None) -> None:
    found = False
    for phase in data["phases"]:
        for item in phase["items"]:
            if item["id"] == item_id:
                item["status"] = status
                if status == "completed":
                    item["notes"] = notes
                    item["error"] = None
                elif status == "failed":
                    item["error"] = error or "Unspecified failure"
                    item["notes"] = notes
                else:
                    item["notes"] = notes
                    item["error"] = None
                found = True
                break
    if not found:
        raise ValueError(f"Unknown item id: {item_id}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", default="research_rubric.json")
    ap.add_argument("--item", required=True)
    ap.add_argument("--status", required=True, choices=["pending", "in_progress", "completed", "failed"])
    ap.add_argument("--notes", default=None)
    ap.add_argument("--error", default=None)
    args = ap.parse_args()

    rubric_path = Path(args.rubric)
    data = json.loads(rubric_path.read_text())
    set_item(data, args.item, args.status, args.notes, args.error)
    recompute_summary(data)
    data["updated_at"] = now_iso()
    rubric_path.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
