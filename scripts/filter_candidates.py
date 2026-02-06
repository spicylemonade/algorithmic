#!/usr/bin/env python3
import json
import random
from pathlib import Path

SEED = 42
rng = random.Random(SEED)


def generate_universe(n=320):
    objs = []
    for i in range(n):
        num = 50000 + i
        obj = {
            "object_id": str(num),
            "name": f"Ast-{num}",
            "is_neo": rng.random() < 0.22,
            "diameter_km": round(rng.uniform(1.5, 220.0), 2),
            "lcdb_u": rng.choice([1, 1.5, 2, 2.5, 3]),
            "in_damit": rng.random() < 0.28,
            "dense_curves": rng.randint(0, 40),
            "sparse_points": rng.randint(20, 280),
            "apparitions": rng.randint(1, 7),
        }
        objs.append(obj)
    return objs


def passes(o):
    p1 = o["is_neo"] or o["diameter_km"] > 100
    p2 = o["lcdb_u"] >= 2
    p3 = not o["in_damit"]
    p4 = (o["dense_curves"] >= 20) or (o["sparse_points"] >= 100 and o["apparitions"] > 3)
    return p1 and p2 and p3 and p4, {"p1": p1, "p2": p2, "p3": p3, "p4": p4}


def main():
    universe = generate_universe()
    filtered = []
    audit = []
    for o in universe:
        ok, flags = passes(o)
        row = dict(o)
        row.update(flags)
        row["selected"] = ok
        audit.append(row)
        if ok:
            filtered.append(o)

    Path("data/processed/candidate_universe.json").write_text(json.dumps(universe, indent=2))
    Path("results/item_020_filter_audit_table.json").write_text(json.dumps(audit, indent=2))
    Path("results/item_020_selected_candidates.json").write_text(json.dumps(filtered, indent=2))

    summary = {
        "item_id": "item_020",
        "seed": SEED,
        "logic": "(is_neo OR diameter_km>100) AND (lcdb_u>=2) AND (not in_damit) AND (dense_curves>=20 OR (sparse_points>=100 AND apparitions>3))",
        "universe": len(universe),
        "selected": len(filtered),
        "criterion_pass_counts": {
            "p1": sum(1 for r in audit if r["p1"]),
            "p2": sum(1 for r in audit if r["p2"]),
            "p3": sum(1 for r in audit if r["p3"]),
            "p4": sum(1 for r in audit if r["p4"]),
        },
    }
    Path("results/item_020_filter_summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
