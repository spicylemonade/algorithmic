#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

from lci.config import set_global_seed
from lci.convex_optimizer import model_mags, optimize_convex, pole_error_deg


def run() -> dict:
    set_global_seed(42)
    rng = np.random.default_rng(42)
    sun = np.array([1.0, 0.1, 0.1])
    obs = np.array([0.4, -0.6, 0.7])

    trial_results = []
    success = 0

    for k in range(10):
        true = np.array([
            rng.uniform(0.8, 1.5),
            rng.uniform(0.6, 1.2),
            rng.uniform(0.5, 1.1),
            rng.uniform(4.0, 12.0),
            rng.uniform(0, 2 * np.pi),
            rng.uniform(-0.9, 0.9),
        ])
        times = np.linspace(0.0, true[3] * 1.6, 120)
        obs_mag = model_mags(true, times, sun, obs) + rng.normal(0.0, 0.005, size=times.size)

        init = true.copy()
        init[:3] *= rng.uniform(0.9, 1.1, size=3)
        init[3] *= rng.uniform(0.95, 1.05)
        init[4] = (init[4] + rng.normal(0, 0.08)) % (2 * np.pi)
        init[5] = float(np.clip(init[5] + rng.normal(0, 0.08), -np.pi / 2, np.pi / 2))

        res = optimize_convex(init, times, obs_mag, sun, obs, iters=16, lr=0.02)
        perr = abs(res.params[3] - true[3]) / true[3] * 100.0
        aerr = pole_error_deg(true[4], true[5], res.params[4], res.params[5])
        ok = (perr <= 0.5) and (aerr <= 10.0)
        success += int(ok)
        trial_results.append({
            "trial": k,
            "period_error_pct": float(perr),
            "pole_error_deg": float(aerr),
            "success": bool(ok),
        })

    return {
        "item_id": "item_007",
        "seed": 42,
        "trials": 10,
        "success_count": success,
        "pass_rate": success / 10.0,
        "acceptance_pass": bool(success >= 8),
        "trial_results": trial_results,
    }


if __name__ == "__main__":
    out = run()
    Path("results/item_007_convex_recovery.json").write_text(json.dumps(out, indent=2) + "\n")
