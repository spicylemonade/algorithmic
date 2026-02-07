from __future__ import annotations

import random
from dataclasses import dataclass

from .photometry import PhotometryModule
from .types import InversionResult, Observation


@dataclass
class EvolutionarySolver:
    seed: int = 42
    generations: int = 80
    pop_size: int = 32

    def refine(self, base_result: InversionResult, observations: list[Observation]) -> InversionResult:
        rng = random.Random(self.seed)
        photo = PhotometryModule()

        best = base_result
        best_loss = photo.residual_rms(best.mesh, best.spin, observations)

        for _ in range(self.generations):
            for _ in range(self.pop_size):
                cand = InversionResult(
                    asteroid_id=best.asteroid_id,
                    mesh=best.mesh,
                    spin=type(best.spin)(
                        lambda_deg=(best.spin.lambda_deg + rng.uniform(-4, 4)) % 360,
                        beta_deg=max(-90, min(90, best.spin.beta_deg + rng.uniform(-2, 2))),
                        period_hours=max(2.0, best.spin.period_hours + rng.uniform(-0.01, 0.01)),
                        phi0_deg=(best.spin.phi0_deg + rng.uniform(-4, 4)) % 360,
                    ),
                    metrics=dict(best.metrics),
                )
                loss = photo.residual_rms(cand.mesh, cand.spin, observations)
                if loss < best_loss:
                    best = cand
                    best_loss = loss

        best.metrics["photometric_rms"] = best_loss
        return best
