#!/usr/bin/env python3
import json
import time
import tracemalloc
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lci.convex_optimizer import model_mags


def run_once(n_points: int) -> tuple[float, float]:
    truth = np.array([1.2, 0.9, 0.7, 6.5, 1.2, 0.25])
    t = np.linspace(0, truth[3] * 1.6, n_points)
    s = np.array([1.0, 0.2, 0.1])
    o = np.array([0.4, -0.5, 0.7])

    tracemalloc.start()
    t0 = time.perf_counter()
    _ = model_mags(truth, t, s, o)
    wall = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return wall, peak / (1024 * 1024)


def main():
    sizes = [60, 120, 240, 480, 960]
    rows = []
    for n in sizes:
        walls = []
        mems = []
        for _ in range(5):
            w, m = run_once(n)
            walls.append(w)
            mems.append(m)
        rows.append({"n_points": n, "wall_time_s": float(np.mean(walls)), "peak_mem_mb": float(np.mean(mems))})

    x = np.array([r["n_points"] for r in rows], dtype=float)
    y = np.array([r["wall_time_s"] for r in rows], dtype=float)
    coef = np.polyfit(x, y, 1)
    pred = coef[0] * x + coef[1]
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2) + 1e-12)
    r2 = 1 - ss_res / ss_tot

    plt.figure(figsize=(7, 4.5))
    plt.plot(x, y, "o-", label="Measured")
    plt.plot(x, pred, "--", label=f"Linear fit R^2={r2:.3f}")
    plt.xlabel("Dataset size (points)")
    plt.ylabel("Wall time (s)")
    plt.title("Item 020 Runtime Scaling")
    plt.legend()
    plt.tight_layout()
    plt.savefig("figures/item_020_scaling.png", dpi=150)

    out = {
        "item_id": "item_020",
        "mode": "optimized_vectorized_model",
        "profiles": rows,
        "linear_fit": {"slope": float(coef[0]), "intercept": float(coef[1]), "r2": r2},
        "acceptance_pass": bool(r2 >= 0.90),
        "figure": "figures/item_020_scaling.png",
    }
    Path("results/item_020_runtime_scaling.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
