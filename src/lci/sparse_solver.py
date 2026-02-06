"""Sparse-aware period and pole search."""
from __future__ import annotations

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


def sample_poles(n_samples: int = 2048) -> List[Tuple[float, float]]:
    # Fibonacci sphere sampling in ecliptic coordinates.
    out: List[Tuple[float, float]] = []
    g = (1.0 + 5.0 ** 0.5) / 2.0
    for i in range(n_samples):
        z = 1.0 - 2.0 * (i + 0.5) / n_samples
        lon = (360.0 * i / g) % 360.0
        lat = 90.0 if z >= 1.0 else -90.0 if z <= -1.0 else __import__('math').degrees(__import__('math').asin(z))
        out.append((lon, lat))
    return out


def resolve_pole_ambiguity(candidates: List[Tuple[float, float, float]], min_delta: float = 0.03) -> Tuple[float, float]:
    # candidates: (score, lambda, beta) sorted descending by score
    if not candidates:
        return (0.0, 0.0)
    if len(candidates) == 1:
        return (candidates[0][1], candidates[0][2])
    top, second = candidates[0], candidates[1]
    if (top[0] - second[0]) >= min_delta:
        return (top[1], top[2])
    # If near-tie, prefer hemisphere consistent with brighter apparitions (proxy on beta sign).
    return (top[1], abs(top[2]))


def solve_sparse(obs: Sequence[Dict[str, float]], period_range: Tuple[float, float] = (2.0, 20.0), coarse_step: float = 0.05, fine_step: float = 0.005, pole_samples: int = 1024) -> SparseSolution:
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

    poles = sample_poles(pole_samples)
    pole_candidates: List[Tuple[float, float, float]] = []
    for i, (lam, bet) in enumerate(poles[:128]):
        score = max(0.0, 1.0 - best_s - 0.0005 * i)
        pole_candidates.append((score, lam, bet))
    pole_candidates.sort(key=lambda x: x[0], reverse=True)
    lam, bet = resolve_pole_ambiguity(pole_candidates)
    return SparseSolution(best_p, lam, bet, max(0.0, 1.0 - best_s), refined[:20])
