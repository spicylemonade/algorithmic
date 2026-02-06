#!/usr/bin/env python3
import argparse, json
from datetime import datetime, timezone


def recalc_summary(r):
    counts = {"completed":0, "in_progress":0, "failed":0, "pending":0}
    total = 0
    for ph in r.get("phases", []):
        for it in ph.get("items", []):
            st = it.get("status", "pending")
            counts[st] = counts.get(st, 0) + 1
            total += 1
    r["summary"] = {
        "total_items": total,
        "completed": counts.get("completed", 0),
        "in_progress": counts.get("in_progress", 0),
        "failed": counts.get("failed", 0),
        "pending": counts.get("pending", 0),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", default="research_rubric.json")
    ap.add_argument("--item-id", required=True)
    ap.add_argument("--status", required=True, choices=["pending","in_progress","completed","failed"])
    ap.add_argument("--notes")
    ap.add_argument("--error")
    args = ap.parse_args()

    with open(args.rubric, "r", encoding="utf-8") as f:
        rubric = json.load(f)

    found = None
    for ph in rubric.get("phases", []):
        for it in ph.get("items", []):
            if it.get("id") == args.item_id:
                found = it
                break
        if found:
            break

    if not found:
        raise SystemExit(f"Item {args.item_id} not found")

    found["status"] = args.status
    if args.notes is not None:
        found["notes"] = args.notes
    if args.error is not None:
        found["error"] = args.error
    if args.status == "completed" and found.get("error"):
        found["error"] = None

    rubric["updated_at"] = datetime.now(timezone.utc).isoformat()
    recalc_summary(rubric)

    with open(args.rubric, "w", encoding="utf-8") as f:
        json.dump(rubric, f, indent=2)
        f.write("\n")

if __name__ == "__main__":
    main()
