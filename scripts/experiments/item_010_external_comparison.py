#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from lci.config import set_global_seed
from lci.convex_optimizer import loss, optimize_convex
from lci.geometry import ellipsoid_points
from lci.metrics import period_error_pct, pole_error_deg, hausdorff_distance


def run() -> dict:
    set_global_seed(42)
    rng = np.random.default_rng(42)
    sun = np.array([1.0, 0.2, 0.1])
    obs = np.array([0.4, -0.6, 0.7])

    results = []
    for i in range(5):
        true = np.array([
            rng.uniform(0.9, 1.3),
            rng.uniform(0.7, 1.1),
            rng.uniform(0.6, 1.0),
            rng.uniform(5.0, 10.0),
            rng.uniform(0, 2 * np.pi),
            rng.uniform(-0.6, 0.6),
        ])
        times = np.linspace(0, true[3] * 1.7, 100)
        obs_mag = __import__('lci.convex_optimizer', fromlist=['model_mags']).model_mags(true, times, sun, obs) + rng.normal(0, 0.01, size=times.size)

        init = true.copy()
        init += rng.normal(0, [0.05, 0.05, 0.05, 0.3, 0.1, 0.1])

        ours = optimize_convex(init, times, obs_mag, sun, obs, iters=12, lr=0.02).params

        def obj(x):
            y = x.copy()
            y[0:3] = np.clip(y[0:3], 0.4, 2.0)
            y[3] = np.clip(y[3], 2.0, 30.0)
            y[4] = (y[4] + 2 * np.pi) % (2 * np.pi)
            y[5] = np.clip(y[5], -np.pi / 2, np.pi / 2)
            return loss(y, times, obs_mag, sun, obs)

        ref = minimize(obj, init, method="Nelder-Mead", options={"maxiter": 200, "xatol": 1e-3, "fatol": 1e-4}).x

        true_pts = ellipsoid_points(*true[:3], n=300)
        our_pts = ellipsoid_points(*ours[:3], n=300)
        ref_pts = ellipsoid_points(*ref[:3], n=300)

        our_period_err = period_error_pct(float(true[3]), float(ours[3]))
        ref_period_err = period_error_pct(float(true[3]), float(ref[3]))
        our_pole_err = pole_error_deg(float(true[4]), float(true[5]), float(ours[4]), float(ours[5]))
        ref_pole_err = pole_error_deg(float(true[4]), float(true[5]), float(ref[4]), float(ref[5]))
        our_mesh = hausdorff_distance(true_pts, our_pts)
        ref_mesh = hausdorff_distance(true_pts, ref_pts)

        results.append({
            "object_index": i,
            "ours": {"period_error_pct": our_period_err, "pole_error_deg": our_pole_err, "hausdorff_distance": our_mesh},
            "reference": {"period_error_pct": ref_period_err, "pole_error_deg": ref_pole_err, "hausdorff_distance": ref_mesh},
            "delta_ours_minus_reference": {
                "period_error_pct": our_period_err - ref_period_err,
                "pole_error_deg": our_pole_err - ref_pole_err,
                "hausdorff_distance": our_mesh - ref_mesh,
            },
        })

    return {
        "item_id": "item_010",
        "seed": 42,
        "objects": 5,
        "reference_impl": "scipy.optimize.minimize (Nelder-Mead)",
        "comparisons": results,
    }


if __name__ == "__main__":
    out = run()
    Path("results/item_010_external_comparison.json").write_text(json.dumps(out, indent=2) + "\n")
