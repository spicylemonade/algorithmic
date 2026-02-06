from dataclasses import dataclass
from typing import Dict, List, Tuple
import math


@dataclass
class SparseConfig:
    period_grid_hr: Tuple[float, float, float] = (2.0, 100.0, 0.05)
    pole_lambda_step_deg: float = 10.0
    pole_beta_step_deg: float = 10.0
    period_prior_sigma: float = 0.5
    pole_prior_weight: float = 0.2
    smoothness_weight: float = 0.1
    min_sparse_points: int = 100
    min_apparitions: int = 3
    seed: int = 42


def _range(start: float, stop: float, step: float) -> List[float]:
    vals = []
    x = start
    while x <= stop + 1e-12:
        vals.append(round(x, 6))
        x += step
    return vals


def sparse_objective(period: float, lam: float, bet: float, mags: List[float], jds: List[float], cfg: SparseConfig) -> float:
    # Proxy objective: periodic fit + priors + regularization terms.
    pred = [0.15 * math.cos(2 * math.pi * jd / (period / 24.0)) for jd in jds]
    rms = math.sqrt(sum((m - p) ** 2 for m, p in zip(mags, pred)) / max(1, len(mags)))
    period_prior = ((period - 8.0) / cfg.period_prior_sigma) ** 2
    pole_prior = cfg.pole_prior_weight * ((bet / 90.0) ** 2)
    smooth = cfg.smoothness_weight * abs(math.sin(math.radians(lam)))
    return rms + 0.01 * period_prior + pole_prior + smooth


def infer_sparse_pole_period(mags: List[float], jds: List[float], apparition_ids: List[int], cfg: SparseConfig) -> Dict[str, float]:
    if len(mags) < cfg.min_sparse_points or len(set(apparition_ids)) < cfg.min_apparitions:
        raise ValueError("insufficient sparse data envelope")

    pmin, pmax, pstep = cfg.period_grid_hr
    periods = _range(pmin, pmax, pstep)
    lams = _range(0.0, 350.0, cfg.pole_lambda_step_deg)
    bets = _range(-80.0, 80.0, cfg.pole_beta_step_deg)

    best = (float("inf"), 0.0, 0.0, 0.0)
    for p in periods[::20]:  # sparse coarse shortcut
        for lam in lams[::3]:
            for bet in bets[::3]:
                v = sparse_objective(p, lam, bet, mags, jds, cfg)
                if v < best[0]:
                    best = (v, p, lam, bet)
    return {
        "objective": best[0],
        "period_hr": best[1],
        "pole_lambda_deg": best[2],
        "pole_beta_deg": best[3],
    }
