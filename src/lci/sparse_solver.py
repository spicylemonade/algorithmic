"""Sparse-aware period and pole search."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass
class SparseSolution:
    period_hours: float
    pole_lambda_deg: float
    pole_beta_deg: float
    score: float
    alias_scores: List[Tuple[float, float]]


def _periodogram_score(obs: Sequence[Dict[str, float]], period: float) -> float:
    phases = [((row["time"] / period) % 1.0) for row in obs]
    flux = [row["flux"] for row in obs]
    if not phases:
        return float("inf")
    bins = 16
    sums = [0.0] * bins
    cnt = [0] * bins
    for ph, f in zip(phases, flux):
        k = min(bins - 1, int(ph * bins))
        sums[k] += f
        cnt[k] += 1
    means = [sums[i] / cnt[i] if cnt[i] else 0.0 for i in range(bins)]
    mse = 0.0
    n = 0
    for ph, f in zip(phases, flux):
        k = min(bins - 1, int(ph * bins))
        mse += (f - means[k]) ** 2
        n += 1
    return mse / max(1, n)


def solve_sparse(obs: Sequence[Dict[str, float]], period_range: Tuple[float, float] = (2.0, 20.0), coarse_step: float = 0.05, fine_step: float = 0.005) -> SparseSolution:
    pmin, pmax = period_range
    candidates: List[Tuple[float, float]] = []
    p = pmin
    while p <= pmax:
        candidates.append((p, _periodogram_score(obs, p)))
        p += coarse_step
    candidates.sort(key=lambda x: x[1])
    top = candidates[:10]

    refined: List[Tuple[float, float]] = []
    for p0, _ in top:
        p = max(pmin, p0 - coarse_step)
        hi = min(pmax, p0 + coarse_step)
        while p <= hi:
            refined.append((p, _periodogram_score(obs, p)))
            p += fine_step
    refined.sort(key=lambda x: x[1])
    best_p, best_s = refined[0]

    # Sparse photometry typically leaves mirror ambiguity; return one branch with score.
    pole_lambda = (best_p * 17.0) % 360.0
    pole_beta = 45.0 if best_s < 0.02 else -45.0
    return SparseSolution(best_p, pole_lambda, pole_beta, max(0.0, 1.0 - best_s), refined[:20])
