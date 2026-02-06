"""Convex inversion core (Kaasalainen-Torppa inspired)."""

from __future__ import annotations


def _objective(state: dict, observations: list[dict]) -> float:
    residual = sum((obs.get("flux", 1.0) - state.get("flux_model", 1.0)) ** 2 for obs in observations)
    smooth_penalty = state.get("smooth_penalty", 0.0)
    return residual + smooth_penalty


def _gradient(state: dict, observations: list[dict]) -> dict:
    # Placeholder gradient to keep baseline deterministic while interfaces settle.
    grad_flux = 2.0 * sum(state.get("flux_model", 1.0) - obs.get("flux", 1.0) for obs in observations)
    return {"flux_model": grad_flux}


def optimize_convex(initial_state: dict, observations: list[dict], config) -> dict:
    state = dict(initial_state)
    state.setdefault("flux_model", 1.0)
    max_iters = getattr(config, "convex_iters", 400)
    grad_tol = 1e-5
    rel_obj_tol = 1e-6
    alpha0 = 1.0
    armijo_c1 = 1e-4
    armijo_tau = 0.5
    prev_obj = _objective(state, observations)

    for it in range(1, max_iters + 1):
        grad = _gradient(state, observations)
        grad_norm = abs(grad["flux_model"])
        if grad_norm < grad_tol:
            return {"state": state, "rms": prev_obj ** 0.5, "iterations": it, "converged": True, "reason": "grad_tol"}

        direction = -grad["flux_model"]
        alpha = alpha0
        while alpha > 1e-8:
            trial = dict(state)
            trial["flux_model"] = state["flux_model"] + alpha * direction
            trial_obj = _objective(trial, observations)
            if trial_obj <= prev_obj + armijo_c1 * alpha * grad["flux_model"] * direction:
                state = trial
                break
            alpha *= armijo_tau

        obj = _objective(state, observations)
        rel_change = abs(prev_obj - obj) / max(prev_obj, 1e-12)
        if rel_change < rel_obj_tol:
            return {"state": state, "rms": obj ** 0.5, "iterations": it, "converged": True, "reason": "rel_obj_tol"}
        prev_obj = obj

    return {"state": state, "rms": prev_obj ** 0.5, "iterations": max_iters, "converged": False, "reason": "max_iters"}
