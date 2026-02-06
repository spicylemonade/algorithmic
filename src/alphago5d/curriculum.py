from __future__ import annotations


def temperature_for_move(move_idx: int) -> float:
    if move_idx < 10:
        return 1.0
    if move_idx < 30:
        return 0.5
    return 0.1


def resignation_threshold(training_step: int) -> float:
    if training_step < 10_000:
        return -0.98
    if training_step < 50_000:
        return -0.95
    return -0.90


def optimizer_ranges() -> dict[str, tuple[float, float]]:
    return {
        "learning_rate": (1e-4, 3e-3),
        "weight_decay": (1e-6, 1e-3),
        "value_loss_coef": (0.5, 2.0),
        "policy_loss_coef": (0.8, 1.2),
    }
