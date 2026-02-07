from dataclasses import dataclass


@dataclass
class HandoffDecision:
    handoff: bool
    reason: str
    rollback: bool


def decide_handoff(
    convergence_slope: float,
    stagnation_steps: int,
    mesh_complexity: float,
    candidate_loss: float,
    baseline_loss: float,
) -> HandoffDecision:
    if convergence_slope > -1e-5 and stagnation_steps >= 25 and mesh_complexity >= 0.3:
        return HandoffDecision(True, "residual stagnation with sufficient complexity", False)

    if convergence_slope > -5e-6 and stagnation_steps >= 40:
        return HandoffDecision(True, "flat convergence", False)

    # Roll back if evolutionary branch regresses by >2%.
    if candidate_loss > baseline_loss * 1.02:
        return HandoffDecision(False, "rollback to convex state", True)

    return HandoffDecision(False, "continue gradient optimization", False)
