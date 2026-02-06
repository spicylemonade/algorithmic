"""Physically informed priors and penalties for inversion."""
from __future__ import annotations

import math
from typing import Dict


def spin_rate_penalty(period_h: float, min_h: float = 2.1, max_h: float = 100.0) -> float:
    if period_h < min_h:
        return ((min_h - period_h) / min_h) ** 2
    if period_h > max_h:
        return ((period_h - max_h) / max_h) ** 2
    return 0.0


def inertia_penalty(axis_a: float, axis_b: float, axis_c: float, max_ratio: float = 4.0) -> float:
    ratio = max(axis_a, axis_b, axis_c) / max(1e-9, min(axis_a, axis_b, axis_c))
    return max(0.0, (ratio - max_ratio) / max_ratio) ** 2


def convexity_relaxation_penalty(concavity_fraction: float, bound: float = 0.35) -> float:
    return max(0.0, (concavity_fraction - bound) / bound) ** 2


def albedo_phase_penalty(g_slope: float, g_min: float = -0.1, g_max: float = 1.0) -> float:
    if g_slope < g_min:
        return (g_min - g_slope) ** 2
    if g_slope > g_max:
        return (g_slope - g_max) ** 2
    return 0.0


def spin_axis_consistency_penalty(delta_deg: float, tol_deg: float = 25.0) -> float:
    return max(0.0, (delta_deg - tol_deg) / tol_deg) ** 2


def density_proxy_penalty(volume: float, spin_h: float, rho_min: float = 0.5, rho_max: float = 8.0) -> float:
    # Proxy relation for cohesionless limit trend, dimensionless scaling for penalty only.
    omega = 2.0 * math.pi / max(1e-9, spin_h)
    rho_proxy = omega * omega * (volume ** (1.0 / 3.0))
    if rho_proxy < rho_min:
        return ((rho_min - rho_proxy) / rho_min) ** 2
    if rho_proxy > rho_max:
        return ((rho_proxy - rho_max) / rho_max) ** 2
    return 0.0


def aggregate_physical_penalty(inputs: Dict[str, float], weights: Dict[str, float] | None = None) -> float:
    w = weights or {
        "spin_rate": 1.0,
        "inertia": 0.6,
        "convexity_relax": 0.5,
        "albedo_phase": 0.4,
        "spin_axis_consistency": 0.7,
        "density_proxy": 0.5,
    }
    penalties = {
        "spin_rate": spin_rate_penalty(inputs["period_h"]),
        "inertia": inertia_penalty(inputs["axis_a"], inputs["axis_b"], inputs["axis_c"]),
        "convexity_relax": convexity_relaxation_penalty(inputs["concavity_fraction"]),
        "albedo_phase": albedo_phase_penalty(inputs["g_slope"]),
        "spin_axis_consistency": spin_axis_consistency_penalty(inputs["spin_axis_delta_deg"]),
        "density_proxy": density_proxy_penalty(inputs["volume"], inputs["period_h"]),
    }
    return sum(w[k] * penalties[k] for k in penalties)
