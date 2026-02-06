"""Sparse-photometry inversion module."""

from __future__ import annotations


def _weighted_residual(period_h: float, pole: tuple[float, float], observations: list[dict]) -> float:
    lam, beta = pole
    residual = 0.0
    for obs in observations:
        sigma = max(obs.get("sigma", 0.05), 1e-3)
        model = (period_h % 10.0) * 0.01 + 0.001 * lam - 0.001 * beta
        residual += ((obs.get("flux", 1.0) - model) / sigma) ** 2
    return residual


def solve_sparse_pole_period(observations: list[dict], config) -> dict:
    min_points = getattr(config, "sparse_min_points", 100)
    if len(observations) < min_points:
        return {
            "pole": None,
            "period_h": None,
            "confidence": 0.0,
            "converged": False,
            "reason": "insufficient_points",
        }

    coarse_periods = [0.5 + 0.5 * i for i in range(200)]
    pole_grid = [(lam, beta) for lam in range(0, 360, 15) for beta in range(-75, 76, 15)]

    best = (float("inf"), None, None)
    for period_h in coarse_periods:
        for pole in pole_grid:
            score = _weighted_residual(period_h, pole, observations)
            if score < best[0]:
                best = (score, period_h, pole)

    conf = 1.0 / (1.0 + best[0] / max(len(observations), 1))
    converged = conf >= 0.80
    return {
        "pole": best[2],
        "period_h": best[1],
        "confidence": conf,
        "converged": converged,
        "reason": "confidence" if converged else "low_confidence",
        "grid": {"period_step_h": 0.5, "pole_step_deg": 15},
    }
