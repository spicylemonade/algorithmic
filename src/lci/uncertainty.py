from dataclasses import dataclass
from typing import Dict, List
import random


@dataclass
class UQConfig:
    n_bootstrap: int = 200
    seed: int = 42


def percentile(values: List[float], q: float) -> float:
    if not values:
        raise ValueError("empty values")
    s = sorted(values)
    idx = int((len(s) - 1) * q)
    return s[idx]


def bootstrap_intervals(samples: List[Dict[str, float]], cfg: UQConfig) -> Dict[str, float]:
    rng = random.Random(cfg.seed)
    periods: List[float] = []
    lambdas: List[float] = []
    betas: List[float] = []

    for _ in range(cfg.n_bootstrap):
        bag = [samples[rng.randrange(len(samples))] for _ in range(len(samples))]
        periods.append(sum(x["period_hr"] for x in bag) / len(bag))
        lambdas.append(sum(x["pole_lambda_deg"] for x in bag) / len(bag))
        betas.append(sum(x["pole_beta_deg"] for x in bag) / len(bag))

    out = {
        "period_p05": percentile(periods, 0.05),
        "period_p95": percentile(periods, 0.95),
        "lambda_p05": percentile(lambdas, 0.05),
        "lambda_p95": percentile(lambdas, 0.95),
        "beta_p05": percentile(betas, 0.05),
        "beta_p95": percentile(betas, 0.95),
    }
    width = (out["period_p95"] - out["period_p05"]) + 0.02 * ((out["lambda_p95"] - out["lambda_p05"]) + (out["beta_p95"] - out["beta_p05"]))
    out["confidence_score"] = max(0.0, min(1.0, 1.0 / (1.0 + width)))
    return out
