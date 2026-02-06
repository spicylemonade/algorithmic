"""End-to-end orchestration for synthetic/pilot inversion runs."""
from __future__ import annotations

import hashlib
import math
import platform
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

from .convex_solver import solve_convex
from .evolutionary_solver import refine_nonconvex
from .geometry import Mesh, mesh_brightness, rotation_matrix_z, mat_vec, uv_sphere


@dataclass
class PilotResult:
    seed: int
    period_true: float
    period_convex: float
    period_evo: float
    loss_convex: float
    loss_evo: float


def _synthetic_observations(seed: int, n: int = 48) -> List[Dict[str, float]]:
    random.seed(seed)
    true_period = 5.3
    base = uv_sphere(4, 8, 1.0)
    radii = [1.0 + 0.15 * math.sin(i * 0.4) for i in range(len(base.vertices))]
    verts = [(v[0] * radii[i], v[1] * radii[i], v[2] * radii[i]) for i, v in enumerate(base.vertices)]
    mesh = Mesh(verts, base.faces)

    rows = []
    for i in range(n):
        t = i * 0.17
        theta = 2.0 * math.pi * ((t / true_period) % 1.0)
        rot = rotation_matrix_z(theta)
        rmesh = Mesh([mat_vec(rot, v) for v in mesh.vertices], mesh.faces)
        sun = (1.0, 0.2, 0.4)
        obs = (-0.1, 1.0, 0.3)
        flux = mesh_brightness(rmesh, sun, obs)
        noisy = flux * (1.0 + random.gauss(0.0, 0.01))
        rows.append({
            "time": t,
            "flux": noisy,
            "sun_x": sun[0], "sun_y": sun[1], "sun_z": sun[2],
            "obs_x": obs[0], "obs_y": obs[1], "obs_z": obs[2],
        })
    return rows


def run_pilot(seed: int = 42) -> PilotResult:
    obs = _synthetic_observations(seed)
    template = uv_sphere(4, 8, 1.0)
    convex = solve_convex(template, obs, seed=seed, iters=20)
    evo = refine_nonconvex(template, obs, convex.radii, convex.period, seed=seed, generations=20, pop_size=20)
    return PilotResult(seed, 5.3, convex.period, evo.period, convex.loss, evo.loss)


def run_manifest(seed: int = 42) -> Dict[str, object]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "package_version": "0.1.0",
        "dataset_hashes": {
            "pilot_dataset": hashlib.sha256(f"pilot_seed_{seed}".encode("utf-8")).hexdigest()
        },
        "software": {
            "core_modules": [
                "src/lci/geometry.py",
                "src/lci/convex_solver.py",
                "src/lci/evolutionary_solver.py",
                "src/lci/sparse_solver.py",
                "src/lci/metrics.py",
                "src/lci/pipeline.py"
            ]
        }
    }
