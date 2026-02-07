#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

from lci.config import set_global_seed
from lci.convex_optimizer import model_mags, pole_error_deg
from lci.sparse_solver import solve_sparse, stable_pole


def run() -> dict:
    set_global_seed(42)
    rng = np.random.default_rng(42)
    sun = np.array([0.9, 0.2, 0.3])
    obs = np.array([0.2, -0.7, 0.6])

    n_targets = 10
    ok_count = 0
    details = []

    for i in range(n_targets):
        truth = np.array([
            rng.uniform(0.9, 1.4),
            rng.uniform(0.7, 1.1),
            rng.uniform(0.6, 1.0),
            rng.uniform(4.5, 11.0),
            rng.uniform(0, 2 * np.pi),
            rng.uniform(-0.7, 0.7),
        ])

        # <=100 sparse points across pseudo-apparitions
        app1 = np.linspace(0.0, truth[3] * 0.5, 30)
        app2 = np.linspace(truth[3] * 1.2, truth[3] * 1.7, 35)
        app3 = np.linspace(truth[3] * 2.8, truth[3] * 3.3, 35)
        t = np.concatenate([app1, app2, app3])

        mags = model_mags(truth, t, sun, obs) + rng.normal(0, 0.01, size=t.size)
        res = solve_sparse(t, mags, sun, obs, restarts=20, seed=42 + i)

        pe = pole_error_deg(truth[4], truth[5], res.params[4], res.params[5])
        st = stable_pole(truth[4], truth[5], res.params[4], res.params[5], tol_deg=15.0)
        ok_count += int(st)
        details.append({
            "target": i,
            "sparse_points": int(t.size),
            "restarts": res.restarts_used,
            "pole_error_deg": float(pe),
            "stable": bool(st),
        })

    rate = ok_count / n_targets
    return {
        "item_id": "item_008",
        "seed": 42,
        "targets": n_targets,
        "stable_count": ok_count,
        "stable_rate": rate,
        "max_restarts": 20,
        "acceptance_pass": bool(rate >= 0.7),
        "details": details,
    }


if __name__ == "__main__":
    out = run()
    Path("results/item_008_sparse_solver.json").write_text(json.dumps(out, indent=2) + "\n")
