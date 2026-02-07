from dataclasses import dataclass


@dataclass
class RetuneDecision:
    proceed: bool
    action: str
    next_weights: dict
    next_period_step: float


def decide_retune(iteration: int, deviation_percent: float, base_weights: dict) -> RetuneDecision:
    max_iter = 6
    if deviation_percent < 5.0:
        return RetuneDecision(True, "validation_pass", base_weights, 1e-4)
    if iteration >= max_iter:
        return RetuneDecision(False, "max_iterations_reached", base_weights, 1e-4)

    tuned = dict(base_weights)
    tuned["w_smooth"] = round(tuned.get("w_smooth", 0.2) * 1.15, 6)
    tuned["w_concavity"] = round(tuned.get("w_concavity", 0.1) * 0.9, 6)
    tuned["w_spin"] = round(tuned.get("w_spin", 0.1) * 1.1, 6)

    next_step = 5e-5 if deviation_percent > 8.0 else 8e-5
    return RetuneDecision(False, "retune_and_repeat", tuned, next_step)
