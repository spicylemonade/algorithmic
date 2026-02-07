#!/usr/bin/env python3
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lci.sparse_pole_search import SparsePoleSearcher, synthetic_sparse_scorer


def main() -> None:
    searcher = SparsePoleSearcher(seed=42)
    cases = [
        {"name": "sparse_case_1", "truth": (120.0, 35.0, 6.12)},
        {"name": "sparse_case_2", "truth": (250.0, -22.0, 11.45)},
        {"name": "sparse_case_3", "truth": (42.0, 58.0, 4.87)},
    ]
    out = []
    for c in cases:
        lon, lat, p = c["truth"]
        scorer = synthetic_sparse_scorer(lon, lat, p)
        sol = searcher.search(scorer, p_range=(2.0, 20.0))
        out.append(
            {
                "case": c["name"],
                "truth": {"lambda_deg": lon, "beta_deg": lat, "period_hours": p},
                "recovered": {
                    "lambda_deg": sol.lambda_deg,
                    "beta_deg": sol.beta_deg,
                    "period_hours": sol.period_hours,
                    "mirror_retained": sol.mirror_retained,
                },
                "errors": {
                    "lambda_abs_deg": abs(sol.lambda_deg - lon),
                    "beta_abs_deg": abs(sol.beta_deg - lat),
                    "period_abs_h": abs(sol.period_hours - p),
                },
            }
        )

    payload = {"item_id": "item_012", "seed": 42, "cases": out}
    Path("results/item_012_sparse_pole_search.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
