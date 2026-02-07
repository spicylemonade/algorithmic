from __future__ import annotations

import math
from typing import Iterable

from .types import Mesh, Observation, SpinState


class PhotometryModule:
    """Simplified photometric forward model for reproducible experiments."""

    def predict_magnitude(self, mesh: Mesh, spin: SpinState, obs: Observation, jd_ref: float) -> float:
        amp = 0.4 + 0.2 * abs(math.sin(math.radians(spin.beta_deg)))
        phase_term = 0.02 * obs.phase_angle_deg
        rot = 2.0 * math.pi * (obs.jd - jd_ref) / (spin.period_hours / 24.0)
        lc_term = amp * math.sin(rot + math.radians(spin.phi0_deg))
        shape_term = 0.001 * (len(mesh.vertices) ** 0.5)
        return 15.0 + phase_term - lc_term - shape_term

    def residual_rms(self, mesh: Mesh, spin: SpinState, obs: Iterable[Observation]) -> float:
        obs_list = list(obs)
        if not obs_list:
            return float("inf")
        jd_ref = obs_list[0].jd
        err2 = 0.0
        for o in obs_list:
            r = o.mag - self.predict_magnitude(mesh, spin, o, jd_ref)
            err2 += r * r
        return (err2 / len(obs_list)) ** 0.5
