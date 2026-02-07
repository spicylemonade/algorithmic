#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

from lci.config import set_global_seed
from lci.evolutionary import evolve_nonconvex
from lci.geometry import ellipsoid_points, peanut_points
from lci.photometry import light_curve


def run() -> dict:
    set_global_seed(42)
    rng = np.random.default_rng(42)
    sun = np.array([1.0, 0.2, 0.2])
    obs = np.array([0.2, -0.5, 0.8])

    tests = []
    gains = []
    for i in range(3):
        true = np.array([1.2 + 0.1 * i, 0.85, 0.75, 0.35 + 0.05 * i])
        period = 6.0 + i
        times = np.linspace(0, period * 1.5, 120)
        truth_pts = peanut_points(*true[:3], neck=true[3], n=400)
        obs_mag = light_curve(truth_pts, period, times, sun, obs) + rng.normal(0, 0.005, size=times.size)

        # Convex baseline: best ellipsoid fit over coarse grid
        best_conv = 1e9
        for a in np.linspace(0.9, 1.5, 6):
            for b in np.linspace(0.6, 1.0, 5):
                for c in np.linspace(0.6, 1.0, 5):
                    pts = ellipsoid_points(a, b, c, n=400)
                    pred = light_curve(pts, period, times, sun, obs)
                    obj = float(np.mean((pred - obs_mag) ** 2))
                    if obj < best_conv:
                        best_conv = obj

        pop = np.column_stack([
            rng.uniform(0.8, 1.6, size=20),
            rng.uniform(0.6, 1.1, size=20),
            rng.uniform(0.6, 1.0, size=20),
            rng.uniform(0.0, 0.6, size=20),
        ])
        evo = evolve_nonconvex(pop, period, times, obs_mag, sun, obs, generations=12, elite=5, seed=42 + i)

        gain = (best_conv - evo.objective) / best_conv * 100.0
        gains.append(gain)
        tests.append({
            "test": i,
            "convex_objective": best_conv,
            "evolutionary_objective": evo.objective,
            "improvement_pct": gain,
        })

    return {
        "item_id": "item_011",
        "seed": 42,
        "tests": tests,
        "mean_improvement_pct": float(np.mean(gains)),
        "acceptance_pass": bool(np.mean(gains) >= 20.0),
    }


if __name__ == "__main__":
    out = run()
    Path("results/item_011_evolutionary.json").write_text(json.dumps(out, indent=2) + "\n")
