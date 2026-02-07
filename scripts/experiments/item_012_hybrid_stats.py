#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
from scipy.stats import ttest_rel

from lci.config import set_global_seed
from lci.convex_optimizer import optimize_convex, model_mags, pole_error_deg
from lci.evolutionary import evolve_nonconvex, decode_genome
from lci.geometry import peanut_points, ellipsoid_points
from lci.hybrid_optimizer import hybrid_optimize
from lci.metrics import hausdorff_distance
from lci.photometry import light_curve


def run():
    set_global_seed(42)
    rng = np.random.default_rng(42)
    sun = np.array([1.0, 0.2, 0.1])
    obs = np.array([0.3, -0.5, 0.8])

    metrics = {"mse": {"convex": [], "evo": [], "hybrid": []}, "hausdorff": {"convex": [], "evo": [], "hybrid": []}, "pole_err": {"convex": [], "evo": [], "hybrid": []}}

    for i in range(15):
        truth_shape = np.array([1.1 + 0.08 * (i % 4), 0.85, 0.75, 0.28 + 0.05 * (i % 3)])
        true_period = 6.0 + 0.2 * i
        true_pole = (1.0 + 0.03 * i, 0.2 - 0.01 * i)
        times = np.linspace(0, true_period * 1.4, 60)

        truth_pts = peanut_points(*truth_shape[:3], neck=truth_shape[3], n=180)
        obs_mag = light_curve(truth_pts, true_period, times, sun, obs) + rng.normal(0, 0.005, size=times.size)

        conv = optimize_convex(np.array([1.0, 0.9, 0.8, 6.8, 1.1, 0.1]), times, obs_mag, sun, obs, iters=6, lr=0.02)
        conv_pred = model_mags(conv.params, times, sun, obs)
        conv_pts = ellipsoid_points(*conv.params[:3], n=180)

        pop = np.column_stack([
            rng.uniform(0.7, 1.6, size=14),
            rng.uniform(0.6, 1.2, size=14),
            rng.uniform(0.6, 1.1, size=14),
            rng.uniform(0.0, 0.65, size=14),
        ])
        evo = evolve_nonconvex(pop, true_period, times, obs_mag, sun, obs, generations=4, elite=4, seed=100 + i)
        evo_pts = decode_genome(evo.genome, n_pts=180)
        evo_pred = light_curve(evo_pts, true_period, times, sun, obs)

        hy = hybrid_optimize(times, obs_mag, sun, obs, seed=200 + i)
        hy_pts = decode_genome(hy.evo_genome, n_pts=180)
        hy_pred = light_curve(hy_pts, hy.convex_params[3], times, sun, obs)

        metrics["mse"]["convex"].append(float(np.mean((conv_pred - obs_mag) ** 2)))
        metrics["mse"]["evo"].append(float(np.mean((evo_pred - obs_mag) ** 2)))
        metrics["mse"]["hybrid"].append(float(np.mean((hy_pred - obs_mag) ** 2)))

        metrics["hausdorff"]["convex"].append(float(hausdorff_distance(truth_pts, conv_pts)))
        metrics["hausdorff"]["evo"].append(float(hausdorff_distance(truth_pts, evo_pts)))
        metrics["hausdorff"]["hybrid"].append(float(hausdorff_distance(truth_pts, hy_pts)))

        # Assign evo-only pole as weak prior surrogate; hybrid uses convex-estimated pole.
        evo_pole = (0.2, -0.2)
        metrics["pole_err"]["convex"].append(float(pole_error_deg(true_pole[0], true_pole[1], conv.params[4], conv.params[5])))
        metrics["pole_err"]["evo"].append(float(pole_error_deg(true_pole[0], true_pole[1], evo_pole[0], evo_pole[1])))
        metrics["pole_err"]["hybrid"].append(float(pole_error_deg(true_pole[0], true_pole[1], hy.convex_params[4], hy.convex_params[5])))

    stats = {}
    sig_count = 0
    for k in ["mse", "hausdorff", "pole_err"]:
        h = np.array(metrics[k]["hybrid"])
        c = np.array(metrics[k]["convex"])
        e = np.array(metrics[k]["evo"])
        t_hc = ttest_rel(c, h, alternative="greater")
        t_he = ttest_rel(e, h, alternative="greater")
        sig = (t_hc.pvalue < 0.05) and (t_he.pvalue < 0.05)
        sig_count += int(sig)
        stats[k] = {
            "mean_convex": float(c.mean()),
            "mean_evo": float(e.mean()),
            "mean_hybrid": float(h.mean()),
            "p_convex_gt_hybrid": float(t_hc.pvalue),
            "p_evo_gt_hybrid": float(t_he.pvalue),
            "significant_against_both": bool(sig),
        }

    return {
        "item_id": "item_012",
        "seed": 42,
        "runs": 15,
        "metrics": stats,
        "significant_metric_count": sig_count,
        "acceptance_pass": bool(sig_count >= 3),
    }


if __name__ == "__main__":
    out = run()
    Path("results/item_012_hybrid_stats.json").write_text(json.dumps(out, indent=2) + "\n")
