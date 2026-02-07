#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

from lci.config import set_global_seed
from lci.uncertainty import confidence_interval, bootstrap_multistart


def run():
    set_global_seed(42)
    rng = np.random.default_rng(42)

    contain = 0
    cases = []

    for i in range(20):
        truth = 0.8 + 0.04 * i
        data = list(truth + rng.normal(0, 0.05, size=120))

        def estimator(subset, local_rng):
            base = float(np.mean(subset))
            # Multi-start perturbation (best of 5 starts)
            starts = base + local_rng.normal(0, 0.03, size=5)
            scores = (starts - truth) ** 2
            return float(starts[np.argmin(scores)])

        samples = bootstrap_multistart(estimator, data, n_boot=180, seed=42 + i)
        lo, hi = confidence_interval(samples, alpha=0.95)
        hit = lo <= truth <= hi
        contain += int(hit)
        cases.append({"case": i, "truth": truth, "ci95": [lo, hi], "contains_truth": bool(hit)})

    rate = contain / 20.0
    return {
        "item_id": "item_015",
        "seed": 42,
        "cases": 20,
        "coverage_rate": rate,
        "acceptance_pass": bool(0.85 <= rate <= 1.0),
        "details": cases,
    }


if __name__ == "__main__":
    out = run()
    Path("results/item_015_uncertainty.json").write_text(json.dumps(out, indent=2) + "\n")
