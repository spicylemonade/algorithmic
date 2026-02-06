#!/usr/bin/env python3
import argparse
import datetime as dt
import json
from pathlib import Path


def refresh_summary(doc: dict) -> None:
    counts = {"completed": 0, "in_progress": 0, "failed": 0, "pending": 0}
    for phase in doc["phases"]:
        for item in phase["items"]:
            status = item["status"]
            if status not in counts:
                counts[status] = 0
            counts[status] += 1
    for key in ["completed", "in_progress", "failed", "pending"]:
        doc["summary"][key] = counts.get(key, 0)
    doc["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()


def set_item_status(path: Path, item_id: str, status: str, notes: str | None, error: str | None) -> None:
    with path.open() as f:
        doc = json.load(f)

    found = False
    for phase in doc["phases"]:
        for item in phase["items"]:
            if item["id"] == item_id:
                item["status"] = status
                item["notes"] = notes
                item["error"] = error
                found = True
                break
        if found:
            break
    if not found:
        raise ValueError(f"Item {item_id} not found")

    refresh_summary(doc)
    with path.open("w") as f:
        json.dump(doc, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update research rubric status for a single item")
    parser.add_argument("--rubric", default="research_rubric.json")
    parser.add_argument("--item", required=True)
    parser.add_argument("--status", required=True, choices=["pending", "in_progress", "completed", "failed"])
    parser.add_argument("--notes")
    parser.add_argument("--error")
    args = parser.parse_args()

    if args.status == "failed" and not args.error:
        raise ValueError("--error is required when status is failed")
    if args.status == "completed" and not args.notes:
        raise ValueError("--notes is required when status is completed")

    set_item_status(Path(args.rubric), args.item, args.status, args.notes, args.error)
