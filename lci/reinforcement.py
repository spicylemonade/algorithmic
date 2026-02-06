"""Recursive optimization refinement controller."""

from __future__ import annotations


def refine_hyperparameters(state: dict, deviation_percent: float) -> dict:
    out = dict(state)
    if deviation_percent > 5.0:
        out["w_phot"] = min(out.get("w_phot", 1.0) * 1.1, 5.0)
        out["w_reg"] = max(out.get("w_reg", 0.5) * 0.9, 0.05)
        out["period_step_h"] = max(out.get("period_step_h", 0.5) * 0.5, 0.01)
        out["action"] = "tighten_search"
    else:
        out["action"] = "promote"
    return out


def reinforcement_loop(initial_state: dict, deviations: list[float]) -> dict:
    state = dict(initial_state)
    history = []
    for i, dev in enumerate(deviations, start=1):
        state = refine_hyperparameters(state, dev)
        history.append({"iteration": i, "deviation_percent": dev, "state": dict(state)})
        if dev <= 5.0:
            break
    return {"final_state": state, "history": history}
