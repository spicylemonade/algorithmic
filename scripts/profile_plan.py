#!/usr/bin/env python3
import cProfile
import pstats
import json
from pathlib import Path

from src.lci.convex_engine import ConvexOptimizer, ConvexParams
from src.lci.interfaces import Observation, Geometry


def synthetic_observations(n: int = 800):
    obs = []
    for i in range(n):
        obs.append(
            Observation(
                jd_tdb=2459000.0 + i * 0.01,
                magnitude=0.05,
                sigma=0.02,
                geometry=Geometry((1, 0, 0), (0, 1, 0), 30.0),
                filter_band="V",
            )
        )
    return obs


def run_once():
    opt = ConvexOptimizer(max_iter=25)
    init = ConvexParams(
        period_hr=8.0,
        pole_lambda_deg=120.0,
        pole_beta_deg=-20.0,
        phase0_rad=0.0,
        shape_coeffs=[0.1] * 16,
        scatter_coeffs=[0.2, 0.1],
    )
    obs = synthetic_observations(300)
    opt.run(obs, init)


def main():
    prof = cProfile.Profile()
    prof.enable()
    run_once()
    prof.disable()
    stats = pstats.Stats(prof).sort_stats("cumtime")
    top = []
    for func, stat in list(stats.stats.items())[:20]:
        filename, lineno, fn_name = func
        cc, nc, tt, ct, callers = stat
        top.append({"function": f"{fn_name}@{filename}:{lineno}", "cumtime": ct})
    Path("results/item_015_profile_raw.json").write_text(json.dumps(top, indent=2))


if __name__ == "__main__":
    main()
