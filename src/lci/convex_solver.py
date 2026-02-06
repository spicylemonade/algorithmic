"""Gradient-style convex inversion core."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .geometry import Mesh, mesh_brightness, rotation_matrix_z, mat_vec


@dataclass
class ConvexState:
    radii: List[float]
    period: float
    pole_lambda: float
    pole_beta: float
    loss: float


def _build_scaled_mesh(template: Mesh, radii: Sequence[float]) -> Mesh:
    verts = []
    for v, r in zip(template.vertices, radii):
        verts.append((v[0] * r, v[1] * r, v[2] * r))
    return Mesh(verts, template.faces)


def _loss(mesh: Mesh, obs: Sequence[Dict[str, float]], period: float, w_smooth: float) -> float:
    pred: List[float] = []
    for row in obs:
        theta = 2.0 * math.pi * ((row["time"] / period) % 1.0)
        rot = rotation_matrix_z(theta)
        rmesh = Mesh([mat_vec(rot, v) for v in mesh.vertices], mesh.faces)
        l = mesh_brightness(
            rmesh,
            (row["sun_x"], row["sun_y"], row["sun_z"]),
            (row["obs_x"], row["obs_y"], row["obs_z"]),
        )
        pred.append(l)
    mse = sum((p - r["flux"]) ** 2 for p, r in zip(pred, obs)) / max(1, len(obs))
    smooth = 0.0
    for i in range(1, len(mesh.vertices)):
        smooth += (mesh.vertices[i][0] - mesh.vertices[i - 1][0]) ** 2
    return mse + w_smooth * smooth / max(1, len(mesh.vertices))


def solve_convex(template: Mesh, obs: Sequence[Dict[str, float]], seed: int = 42, iters: int = 120) -> ConvexState:
    random.seed(seed)
    radii = [1.0 for _ in template.vertices]
    period = 4.0
    lr = 0.05
    eps = 1e-3
    best = ConvexState(list(radii), period, 0.0, 0.0, float("inf"))

    for _ in range(iters):
        mesh = _build_scaled_mesh(template, radii)
        base = _loss(mesh, obs, period, w_smooth=0.02)
        if base < best.loss:
            best = ConvexState(list(radii), period, 0.0, 0.0, base)

        grads = [0.0] * len(radii)
        for i in range(0, len(radii), max(1, len(radii) // 48)):
            old = radii[i]
            radii[i] = old + eps
            lp = _loss(_build_scaled_mesh(template, radii), obs, period, w_smooth=0.02)
            radii[i] = old - eps
            lm = _loss(_build_scaled_mesh(template, radii), obs, period, w_smooth=0.02)
            radii[i] = old
            grads[i] = (lp - lm) / (2.0 * eps)

        for i, g in enumerate(grads):
            if g != 0.0:
                radii[i] = max(0.4, min(1.8, radii[i] - lr * g))

        p_plus = period + 1e-3
        p_minus = max(0.1, period - 1e-3)
        g_period = (
            _loss(_build_scaled_mesh(template, radii), obs, p_plus, w_smooth=0.02)
            - _loss(_build_scaled_mesh(template, radii), obs, p_minus, w_smooth=0.02)
        ) / 2e-3
        period = max(0.1, period - 0.02 * g_period)

    return best
