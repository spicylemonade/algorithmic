#!/usr/bin/env python3
import argparse
import datetime
import json
from pathlib import Path


def recompute_summary(data: dict) -> None:
    counts = {"completed": 0, "in_progress": 0, "failed": 0, "pending": 0}
    for phase in data["phases"]:
        for item in phase["items"]:
            counts[item["status"]] += 1
    data["summary"].update(counts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Update research rubric item status")
    parser.add_argument("--file", default="research_rubric.json")
    parser.add_argument("--item", required=True)
    parser.add_argument("--status", choices=["pending", "in_progress", "completed", "failed"], required=True)
    parser.add_argument("--notes", default=None)
    parser.add_argument("--error", default=None)
    args = parser.parse_args()

    rubric_path = Path(args.file)
    data = json.loads(rubric_path.read_text())

    found = False
    for phase in data["phases"]:
        for item in phase["items"]:
            if item["id"] == args.item:
                item["status"] = args.status
                item["notes"] = args.notes
                item["error"] = args.error
                found = True
                break
    if not found:
        raise SystemExit(f"Item {args.item} not found")

    data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    recompute_summary(data)
    rubric_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"updated {args.item} -> {args.status}")


if __name__ == "__main__":
    main()
