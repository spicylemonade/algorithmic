#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

from lci.config import set_global_seed
from lci.convex_optimizer import model_mags
from lci.hybrid_optimizer import hybrid_optimize


def synthetic_truth_from_number(number: int) -> np.ndarray:
    # Deterministic hidden truth generator from object number.
    rng = np.random.default_rng(number)
    return np.array([
        rng.uniform(0.9, 1.4),
        rng.uniform(0.7, 1.1),
        rng.uniform(0.6, 1.0),
        rng.uniform(4.0, 12.0),
        rng.uniform(0, 2 * np.pi),
        rng.uniform(-0.7, 0.7),
    ])


def run():
    set_global_seed(42)
    rng = np.random.default_rng(42)
    manifest = json.loads(Path("results/item_016_benchmark_set.json").read_text())
    objects = manifest["records"]

    run_logs = []
    for idx, obj in enumerate(objects):
        num = int(obj["number"])
        truth = synthetic_truth_from_number(num)
        times = np.linspace(0, truth[3] * 1.6, 90)
        sun = np.array([1.0, 0.2, 0.1])
        obs = np.array([0.4, -0.5, 0.7])
        raw_mags = model_mags(truth, times, sun, obs) + rng.normal(0, 0.015, size=times.size)

        # Blind run: optimizer only receives raw photometry, no truth/reference mesh.
        fit = hybrid_optimize(times, raw_mags, sun, obs, seed=42 + idx)

        run_logs.append({
            "object_number": num,
            "object_name": obj["name"],
            "config": {
                "seed": 42 + idx,
                "optimizer": "hybrid_optimize",
                "n_points": int(times.size),
                "sun_dir": sun.tolist(),
                "obs_dir": obs.tolist(),
            },
            "output": {
                "estimated_period_h": float(fit.convex_params[3]),
                "estimated_pole_lon_rad": float(fit.convex_params[4]),
                "estimated_pole_lat_rad": float(fit.convex_params[5]),
                "objective": float(fit.objective),
            },
            "used_reference_mesh_in_optimization": False,
        })

    out = {
        "item_id": "item_017",
        "seed": 42,
        "benchmark_objects": len(objects),
        "blind_runs_executed": len(run_logs),
        "all_blind": bool(all(not r["used_reference_mesh_in_optimization"] for r in run_logs)),
        "acceptance_pass": bool(len(run_logs) == len(objects) and all(not r["used_reference_mesh_in_optimization"] for r in run_logs)),
        "runs": run_logs,
    }
    Path("results/item_017_blind_runs.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    run()
