from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .convex_optimizer import optimize_convex
from .evolutionary import evolve_nonconvex


@dataclass
class HybridResult:
    convex_params: np.ndarray
    evo_genome: np.ndarray
    objective: float


def hybrid_optimize(times_h, mags, sun_dir, obs_dir, seed: int = 42) -> HybridResult:
    init = np.array([1.1, 0.9, 0.8, 7.0, 1.0, 0.2])
    conv = optimize_convex(init, times_h, mags, sun_dir, obs_dir, iters=12, lr=0.02)

    rng = np.random.default_rng(seed)
    pop = np.column_stack([
        rng.normal(conv.params[0], 0.08, size=24),
        rng.normal(conv.params[1], 0.08, size=24),
        rng.normal(conv.params[2], 0.08, size=24),
        rng.uniform(0.1, 0.6, size=24),
    ])
    pop[:, 0:3] = np.clip(pop[:, 0:3], 0.5, 1.8)
    evo = evolve_nonconvex(pop[:16], conv.params[3], times_h, mags, sun_dir, obs_dir, generations=5, elite=4, seed=seed)
    return HybridResult(convex_params=conv.params, evo_genome=evo.genome, objective=evo.objective)
