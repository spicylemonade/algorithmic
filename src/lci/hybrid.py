"""Hybrid schedule combining convex initialization and GA refinement."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class HandoffDecision:
    switch_to_evolutionary: bool
    reason: str
    plateau_window: int
    residual_autocorr: float


def should_handoff(loss_history: List[float], residual_autocorr: float, plateau_eps: float = 1e-4, plateau_window: int = 12, residual_threshold: float = 0.25) -> HandoffDecision:
    if len(loss_history) < plateau_window + 1:
        return HandoffDecision(False, "insufficient_history", plateau_window, residual_autocorr)
    recent = loss_history[-plateau_window:]
    improvement = max(recent) - min(recent)
    plateau = improvement < plateau_eps
    structured_residual = abs(residual_autocorr) > residual_threshold
    if plateau and structured_residual:
        return HandoffDecision(True, "plateau_and_structured_residual", plateau_window, residual_autocorr)
    if plateau:
        return HandoffDecision(True, "plateau_only", plateau_window, residual_autocorr)
    return HandoffDecision(False, "continue_convex", plateau_window, residual_autocorr)


def default_hybrid_schedule() -> Dict[str, object]:
    return {
        "stage_1": {
            "name": "convex_initialization",
            "max_iters": 150,
            "stop_on_plateau_eps": 1e-4,
            "plateau_window": 12
        },
        "handoff": {
            "requires_plateau": True,
            "residual_autocorr_threshold": 0.25,
            "minimum_signal_to_noise": 3.0
        },
        "stage_2": {
            "name": "evolutionary_refinement",
            "generations": 350,
            "population": 120,
            "convexity_penalty_anneal": [1.0, 0.1]
        }
    }
