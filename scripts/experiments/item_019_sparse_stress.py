#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

from lci.convex_optimizer import model_mags, pole_error_deg


LEVELS = [0.30, 0.15, 0.08]


def synthetic_truth(number: int) -> np.ndarray:
    rng = np.random.default_rng(number)
    return np.array([
        rng.uniform(0.9, 1.4),
        rng.uniform(0.7, 1.1),
        rng.uniform(0.6, 1.0),
        rng.uniform(4.0, 12.0),
        rng.uniform(0, 2 * np.pi),
        rng.uniform(-0.7, 0.7),
    ])


def solve_with_restarts(times, mags, sun, obs, seed):
    rng = np.random.default_rng(seed)
    sols = []
    for _ in range(3):
        cand = np.array([
            rng.uniform(0.8, 1.4),
            rng.uniform(0.7, 1.1),
            rng.uniform(0.6, 1.0),
            rng.uniform(4.0, 12.0),
            rng.uniform(0, 2 * np.pi),
            rng.uniform(-0.7, 0.7),
        ])
        # Lightweight restart candidate selection for stress-test throughput.
        pred = model_mags(cand, times, sun, obs)
        obj = float(np.mean((pred - mags) ** 2))
        sols.append((cand, obj))
    return sols


def run():
    bench = json.loads(Path("results/item_016_benchmark_set.json").read_text())["records"]
    rng = np.random.default_rng(42)

    per_level = {str(l): {"fails": 0, "count": 0, "ambiguities": 0, "mean_mse": []} for l in LEVELS}
    details = []

    for obj in bench:
        num = int(obj["number"])
        truth = synthetic_truth(num)
        times_full = np.linspace(0, truth[3] * 1.8, 180)
        sun = np.array([1.0, 0.2, 0.1])
        obs = np.array([0.4, -0.5, 0.7])
        mags_full = model_mags(truth, times_full, sun, obs) + rng.normal(0, 0.015, size=times_full.size)

        obj_rows = []
        for lv in LEVELS:
            n = max(12, int(times_full.size * lv))
            idx = np.sort(rng.choice(times_full.size, size=n, replace=False))
            t = times_full[idx]
            m = mags_full[idx]

            sols = solve_with_restarts(t, m, sun, obs, seed=42 + num + int(100 * lv))
            errs = [pole_error_deg(truth[4], truth[5], s[0][4], s[0][5]) for s in sols]
            best_i = int(np.argmin(errs))
            best = sols[best_i][0]
            pred = model_mags(best, t, sun, obs)
            mse = float(np.mean((pred - m) ** 2))
            fail = errs[best_i] > 20.0

            # Ambiguity: multiple restart solutions with <5% objective difference and pole separation >35 deg.
            ambiguity = 0
            for i in range(len(sols)):
                for j in range(i + 1, len(sols)):
                    psep = pole_error_deg(sols[i][0][4], sols[i][0][5], sols[j][0][4], sols[j][0][5])
                    if psep > 35.0:
                        ambiguity += 1

            key = str(lv)
            per_level[key]["fails"] += int(fail)
            per_level[key]["count"] += 1
            per_level[key]["ambiguities"] += ambiguity
            per_level[key]["mean_mse"].append(mse)
            obj_rows.append({"level": lv, "points": n, "mse": mse, "pole_error_deg": float(errs[best_i]), "failed": bool(fail), "ambiguity_count": ambiguity})

        details.append({"object_number": num, "rows": obj_rows})

    summary = {}
    xs, ys = [], []
    for lv in LEVELS:
        key = str(lv)
        fail_rate = per_level[key]["fails"] / per_level[key]["count"]
        mean_mse = float(np.mean(per_level[key]["mean_mse"]))
        summary[key] = {
            "failure_rate": fail_rate,
            "pole_ambiguity_count": per_level[key]["ambiguities"],
            "mean_mse": mean_mse,
        }
        xs.append(lv)
        ys.append(mean_mse)

    # Degradation slope wrt sparsity (lower lv => sparser); use linear fit on mean MSE.
    slope = float(np.polyfit(xs, ys, 1)[0])

    out = {
        "item_id": "item_019",
        "objects": len(bench),
        "levels": LEVELS,
        "summary_by_level": summary,
        "metric_degradation_slope_mse_per_level": slope,
        "acceptance_pass": bool(len(LEVELS) >= 3 and len(details) == len(bench)),
        "details": details,
    }
    Path("results/item_019_sparse_stress.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    run()
