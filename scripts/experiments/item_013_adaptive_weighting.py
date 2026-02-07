#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

from lci.adaptive_loss import adaptive_weights
from lci.config import set_global_seed
from lci.convex_optimizer import model_mags, pole_error_deg


def estimate_pole(times, mags, sun, obs, period, sparse_mask, adaptive=False, seed=0):
    rng = np.random.default_rng(seed)
    best_obj = np.inf
    best = None
    for _ in range(100):
        lon = rng.uniform(0, 2 * np.pi)
        lat = rng.uniform(-0.8, 0.8)
        p = np.array([1.1, 0.9, 0.8, period, lon, lat])
        pred = model_mags(p, times, sun, obs)
        resid = pred - mags
        dense_resid = resid[~sparse_mask]
        sparse_resid = resid[sparse_mask]
        if adaptive:
            wd, ws = adaptive_weights(dense_resid.size, sparse_resid.size)
        else:
            wd, ws = (1.0, 1.0)
        obj = wd * np.mean(dense_resid ** 2) + ws * np.mean(sparse_resid ** 2)
        if obj < best_obj:
            best_obj = obj
            best = (lon, lat)
    return best


def run():
    set_global_seed(42)
    rng = np.random.default_rng(42)
    sun = np.array([1.0, 0.15, 0.1])
    obs = np.array([0.3, -0.6, 0.7])

    pole_err_base = []
    pole_err_adapt = []
    dense_chi_base = []
    dense_chi_adapt = []

    for i in range(15):
        true = np.array([1.2, 0.9, 0.7, 6.2 + 0.1 * i, 0.9 + 0.05 * i, 0.25 - 0.01 * i])
        t_dense = np.linspace(0, true[3] * 1.3, 80)
        t_sparse = np.linspace(true[3] * 2.3, true[3] * 3.0, 40)
        t = np.concatenate([t_dense, t_sparse])
        sparse_mask = np.zeros(t.shape[0], dtype=bool)
        sparse_mask[len(t_dense):] = True

        mags = model_mags(true, t, sun, obs)
        mags[: len(t_dense)] += rng.normal(0, 0.008, size=len(t_dense))
        mags[len(t_dense):] += rng.normal(0, 0.02, size=len(t_sparse))

        b_lon, b_lat = estimate_pole(t, mags, sun, obs, true[3], sparse_mask, adaptive=False, seed=100 + i)
        a_lon, a_lat = estimate_pole(t, mags, sun, obs, true[3], sparse_mask, adaptive=True, seed=100 + i)

        pole_err_base.append(pole_error_deg(true[4], true[5], b_lon, b_lat))
        pole_err_adapt.append(pole_error_deg(true[4], true[5], a_lon, a_lat))

        pb = model_mags(np.array([1.1, 0.9, 0.8, true[3], b_lon, b_lat]), t_dense, sun, obs)
        pa = model_mags(np.array([1.1, 0.9, 0.8, true[3], a_lon, a_lat]), t_dense, sun, obs)
        ob = mags[: len(t_dense)]
        dense_chi_base.append(float(np.mean(((pb - ob) / 0.03) ** 2)))
        dense_chi_adapt.append(float(np.mean(((pa - ob) / 0.03) ** 2)))

    med_base = float(np.median(pole_err_base))
    med_adapt = float(np.median(pole_err_adapt))
    reduction = (med_base - med_adapt) / med_base * 100.0
    chi_base = float(np.median(dense_chi_base))
    chi_adapt = float(np.median(dense_chi_adapt))
    chi_worsen = (chi_adapt - chi_base) / chi_base * 100.0

    return {
        "item_id": "item_013",
        "seed": 42,
        "runs": 15,
        "median_pole_error_base_deg": med_base,
        "median_pole_error_adaptive_deg": med_adapt,
        "pole_error_reduction_pct": reduction,
        "median_dense_chi_base": chi_base,
        "median_dense_chi_adaptive": chi_adapt,
        "dense_chi_worsening_pct": chi_worsen,
        "acceptance_pass": bool((reduction >= 15.0) and (chi_worsen <= 5.0)),
    }


if __name__ == "__main__":
    out = run()
    Path("results/item_013_adaptive_weighting.json").write_text(json.dumps(out, indent=2) + "\n")
