#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

from lci.config import set_global_seed
from lci.priors import is_physically_plausible


def run():
    set_global_seed(42)
    rng = np.random.default_rng(42)

    fail_cases = []
    for _ in range(100):
        p = np.array([
            rng.uniform(0.1, 5.0),
            rng.uniform(0.1, 5.0),
            rng.uniform(0.1, 5.0),
            rng.uniform(0.2, 5.0),
            rng.uniform(-1.0, 8.0),
            rng.uniform(-2.0, 2.0),
        ])
        # Force at least one failure condition.
        j = rng.integers(0, 3)
        p[j] = rng.uniform(0.05, 0.2)
        fail_cases.append(p)

    control_cases = []
    for _ in range(100):
        p = np.array([
            rng.uniform(0.7, 1.8),
            rng.uniform(0.7, 1.6),
            rng.uniform(0.6, 1.5),
            rng.uniform(2.5, 12.0),
            rng.uniform(0.0, 2 * np.pi),
            rng.uniform(-1.2, 1.2),
        ])
        p[5] = np.clip(p[5], -np.pi / 2, np.pi / 2)
        control_cases.append(p)

    reject_rate = float(np.mean([not is_physically_plausible(p) for p in fail_cases]))
    preserve_rate = float(np.mean([is_physically_plausible(p) for p in control_cases]))

    return {
        "item_id": "item_014",
        "seed": 42,
        "injected_failure_cases": 100,
        "control_cases": 100,
        "reject_rate": reject_rate,
        "preserve_rate": preserve_rate,
        "acceptance_pass": bool((reject_rate >= 0.90) and (preserve_rate >= 0.95)),
    }


if __name__ == "__main__":
    out = run()
    Path("results/item_014_priors_validation.json").write_text(json.dumps(out, indent=2) + "\n")
