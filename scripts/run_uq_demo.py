#!/usr/bin/env python3
import json
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lci.uncertainty import summarize_ensemble


def main() -> None:
    rng = random.Random(42)
    ensemble = []
    for _ in range(64):
        ensemble.append(
            {
                "lambda_deg": 120 + rng.uniform(-8, 8),
                "beta_deg": 35 + rng.uniform(-5, 5),
                "period_hours": 6.12 + rng.uniform(-0.04, 0.04),
                "axis_a": 16.0 + rng.uniform(-0.8, 0.8),
                "axis_b": 13.5 + rng.uniform(-0.7, 0.7),
                "axis_c": 11.2 + rng.uniform(-0.6, 0.6),
            }
        )

    summary = summarize_ensemble(ensemble)
    payload = {"item_id": "item_014", "seed": 42, "n_starts": len(ensemble), "ci95": summary}
    Path("results/item_014_uncertainty_framework.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
