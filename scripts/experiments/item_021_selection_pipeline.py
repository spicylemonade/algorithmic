#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np

from lci.selection import Candidate, evaluate_rules


def run():
    rng = np.random.default_rng(42)
    rows = []
    for i in range(120):
        c = Candidate(
            object_id=f"OBJ-{10000+i}",
            is_neo=bool(rng.random() < 0.35),
            diameter_km=float(rng.uniform(10, 220)),
            lcdb_u=float(rng.choice([1.5, 2.0, 2.5, 3.0])),
            in_damit=bool(rng.random() < 0.25),
            n_lightcurves=int(rng.integers(5, 45)),
            n_sparse_points=int(rng.integers(30, 220)),
            n_apparitions=int(rng.integers(1, 7)),
        )
        rules = evaluate_rules(c)
        rows.append({
            "object_id": c.object_id,
            "is_neo": c.is_neo,
            "diameter_km": c.diameter_km,
            "lcdb_u": c.lcdb_u,
            "in_damit": c.in_damit,
            "n_lightcurves": c.n_lightcurves,
            "n_sparse_points": c.n_sparse_points,
            "n_apparitions": c.n_apparitions,
            **rules,
        })

    out = {
        "item_id": "item_021",
        "seed": 42,
        "n_objects": len(rows),
        "passes_all_count": int(sum(r["passes_all"] for r in rows)),
        "acceptance_pass": bool(all(all(k in r for k in ["priority_1", "priority_2", "priority_3", "priority_4", "passes_all"]) for r in rows)),
        "candidates": rows,
    }
    Path("results/item_021_candidates.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    run()
