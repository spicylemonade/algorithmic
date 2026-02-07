from __future__ import annotations

from dataclasses import dataclass

from .geometry import GeometryModule
from .photometry import PhotometryModule
from .types import InversionResult, Observation, SpinState


@dataclass
class ConvexSolver:
    step_size: float = 0.05
    max_iter: int = 300

    def solve(self, asteroid_id: str, observations: list[Observation]) -> InversionResult:
        geom = GeometryModule()
        photo = PhotometryModule()
        mesh = geom.ellipsoid_mesh(1.0, 0.9, 0.8)
        spin = SpinState(lambda_deg=120.0, beta_deg=35.0, period_hours=6.0, phi0_deg=0.0)

        for _ in range(self.max_iter):
            base = photo.residual_rms(mesh, spin, observations)
            trial = SpinState(
                lambda_deg=spin.lambda_deg,
                beta_deg=max(-90.0, min(90.0, spin.beta_deg + self.step_size)),
                period_hours=max(2.0, spin.period_hours - 0.001),
                phi0_deg=spin.phi0_deg + 0.2,
            )
            new_loss = photo.residual_rms(mesh, trial, observations)
            if new_loss < base:
                spin = trial
            else:
                self.step_size *= 0.95
                if self.step_size < 1e-4:
                    break

        rms = photo.residual_rms(mesh, spin, observations)
        return InversionResult(asteroid_id=asteroid_id, mesh=mesh, spin=spin, metrics={"photometric_rms": rms})
