"""Adaptive self-reinforcement loop for validation-driven retuning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple


@dataclass
class RetryRecord:
    attempt: int
    deviation: float
    weights: Dict[str, float]
    accepted: bool


@dataclass
class ReinforcementResult:
    passed: bool
    best_deviation: float
    best_weights: Dict[str, float]
    history: List[RetryRecord]


def adapt_weights(weights: Dict[str, float], deviation: float, threshold: float = 0.05) -> Dict[str, float]:
    out = dict(weights)
    if deviation > threshold:
        factor = min(2.0, 1.0 + (deviation - threshold) * 10.0)
        out["w_sparse"] = min(2.0, out.get("w_sparse", 0.25) * factor)
        out["w_phys"] = min(1.0, out.get("w_phys", 0.1) * (1.0 + 0.5 * (factor - 1.0)))
        out["period_granularity"] = max(0.001, out.get("period_granularity", 0.005) * 0.75)
    return out


def self_reinforce(evaluate_fn: Callable[[Dict[str, float], int], float], initial_weights: Dict[str, float], threshold: float = 0.05, max_retries: int = 5) -> ReinforcementResult:
    current = dict(initial_weights)
    best_weights = dict(initial_weights)
    best_dev = float("inf")
    history: List[RetryRecord] = []

    for attempt in range(1, max_retries + 1):
        dev = evaluate_fn(current, attempt)
        accepted = dev <= threshold
        history.append(RetryRecord(attempt, dev, dict(current), accepted))
        if dev < best_dev:
            best_dev = dev
            best_weights = dict(current)
        if accepted:
            return ReinforcementResult(True, best_dev, best_weights, history)

        proposed = adapt_weights(current, dev, threshold)
        # Rollback logic: if adaptation worsens by >10% on next attempt, keep best known weights.
        if attempt >= 2 and dev > history[-2].deviation * 1.1:
            current = dict(best_weights)
        else:
            current = proposed

    return ReinforcementResult(False, best_dev, best_weights, history)
