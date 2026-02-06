from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class SearchConfig:
    period_min_hr: float = 2.0
    period_max_hr: float = 100.0
    coarse_period_step_hr: float = 0.05
    fine_period_step_hr: float = 0.002
    coarse_lambda_step_deg: float = 15.0
    fine_lambda_step_deg: float = 3.0
    coarse_beta_step_deg: float = 15.0
    fine_beta_step_deg: float = 3.0
    convergence_tol: float = 1e-5
    seed: int = 42


def generate_grid(start: float, stop: float, step: float) -> List[float]:
    vals: List[float] = []
    x = start
    while x <= stop + 1e-12:
        vals.append(round(x, 6))
        x += step
    return vals


def coarse_to_fine_schedule(config: SearchConfig) -> Dict[str, List[Tuple[float, float, float]]]:
    coarse: List[Tuple[float, float, float]] = []
    fine: List[Tuple[float, float, float]] = []

    periods = generate_grid(config.period_min_hr, config.period_max_hr, config.coarse_period_step_hr)
    lambdas = generate_grid(0.0, 345.0, config.coarse_lambda_step_deg)
    betas = generate_grid(-75.0, 75.0, config.coarse_beta_step_deg)
    for p in periods:
        coarse.append((p, lambdas[0], betas[0]))

    fine_periods = generate_grid(0.0, 0.2, config.fine_period_step_hr)
    fine_lambdas = generate_grid(-12.0, 12.0, config.fine_lambda_step_deg)
    fine_betas = generate_grid(-12.0, 12.0, config.fine_beta_step_deg)
    for fp in fine_periods:
        fine.append((fp, fine_lambdas[0], fine_betas[0]))

    return {"coarse": coarse, "fine": fine}
