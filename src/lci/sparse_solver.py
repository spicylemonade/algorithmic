from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .convex_optimizer import loss, pole_error_deg


@dataclass
class SparseSolveResult:
    params: np.ndarray
    objective: float
    restarts_used: int


def solve_sparse(
    times_h: np.ndarray,
    mags: np.ndarray,
    sun_dir: np.ndarray,
    obs_dir: np.ndarray,
    restarts: int = 20,
    seed: int = 42,
) -> SparseSolveResult:
    rng = np.random.default_rng(seed)
    best = None
    best_obj = np.inf

    for r in range(restarts):
        p = np.array([
            rng.uniform(0.8, 1.5),
            rng.uniform(0.6, 1.2),
            rng.uniform(0.5, 1.1),
            rng.uniform(4.0, 12.0),
            rng.uniform(0.0, 2 * np.pi),
            rng.uniform(-0.8, 0.8),
        ])
        cur = loss(p, times_h, mags, sun_dir, obs_dir)
        for _ in range(24):
            cand = p + rng.normal(0.0, [0.05, 0.05, 0.05, 0.2, 0.08, 0.08], size=6)
            cand[0:3] = np.clip(cand[0:3], 0.4, 2.0)
            cand[3] = np.clip(cand[3], 2.0, 30.0)
            cand[4] = (cand[4] + 2 * np.pi) % (2 * np.pi)
            cand[5] = np.clip(cand[5], -np.pi / 2, np.pi / 2)
            cobj = loss(cand, times_h, mags, sun_dir, obs_dir)
            if cobj < cur:
                p, cur = cand, cobj
        if cur < best_obj:
            best_obj = cur
            best = SparseSolveResult(params=p, objective=cur, restarts_used=r + 1)

    return best


def stable_pole(true_lon: float, true_lat: float, est_lon: float, est_lat: float, tol_deg: float = 15.0) -> bool:
    return pole_error_deg(true_lon, true_lat, est_lon, est_lat) <= tol_deg
