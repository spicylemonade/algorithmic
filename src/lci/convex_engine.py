from dataclasses import dataclass
from typing import List, Tuple
import math

from .interfaces import Observation, ConvexParams, Mesh


@dataclass
class ForwardModel:
    epsilon: float = 1e-10

    def predict_magnitude(self, obs: Observation, params: ConvexParams) -> float:
        # Minimal deterministic placeholder for interface validation.
        amp = 0.1 + 0.01 * sum(abs(x) for x in params.shape_coeffs[:3])
        phase = 2.0 * math.pi * (obs.jd_tdb / (params.period_hr / 24.0)) + params.phase0_rad
        lc = 1.0 + amp * math.cos(phase)
        return -2.5 * math.log10(max(lc, self.epsilon))


@dataclass
class GradientEvaluator:
    step: float = 1e-4

    def finite_difference(self, observations: List[Observation], params: ConvexParams) -> List[float]:
        # Returns gradient over shape coefficients only in baseline.
        base = self._loss(observations, params)
        grads = []
        for i in range(len(params.shape_coeffs)):
            p = ConvexParams(
                period_hr=params.period_hr,
                pole_lambda_deg=params.pole_lambda_deg,
                pole_beta_deg=params.pole_beta_deg,
                phase0_rad=params.phase0_rad,
                shape_coeffs=list(params.shape_coeffs),
                scatter_coeffs=list(params.scatter_coeffs),
            )
            p.shape_coeffs[i] += self.step
            grads.append((self._loss(observations, p) - base) / self.step)
        return grads

    def _loss(self, observations: List[Observation], params: ConvexParams) -> float:
        fm = ForwardModel()
        s = 0.0
        for obs in observations:
            r = obs.magnitude - fm.predict_magnitude(obs, params)
            s += r * r
        return s / max(len(observations), 1)


@dataclass
class ConvexOptimizer:
    learning_rate: float = 1e-2
    max_iter: int = 200
    tolerance: float = 1e-6

    def run(self, observations: List[Observation], init_params: ConvexParams) -> ConvexParams:
        ge = GradientEvaluator()
        p = ConvexParams(**init_params.__dict__)
        prev = float("inf")
        for _ in range(self.max_iter):
            grads = ge.finite_difference(observations, p)
            for i, g in enumerate(grads):
                p.shape_coeffs[i] -= self.learning_rate * g
            cur = ge._loss(observations, p)
            if abs(prev - cur) < self.tolerance:
                break
            prev = cur
        return p

    def to_mesh(self, params: ConvexParams, n_lon: int = 16, n_lat: int = 8) -> Mesh:
        vertices: List[Tuple[float, float, float]] = []
        faces: List[Tuple[int, int, int]] = []
        for i in range(n_lat + 1):
            lat = -math.pi / 2 + math.pi * i / n_lat
            for j in range(n_lon):
                lon = 2 * math.pi * j / n_lon
                r = 1.0 + 0.05 * math.cos(2 * lon) * math.cos(lat)
                x = r * math.cos(lat) * math.cos(lon)
                y = r * math.cos(lat) * math.sin(lon)
                z = r * math.sin(lat)
                vertices.append((x, y, z))
        for i in range(n_lat):
            for j in range(n_lon):
                a = i * n_lon + j
                b = i * n_lon + (j + 1) % n_lon
                c = (i + 1) * n_lon + j
                d = (i + 1) * n_lon + (j + 1) % n_lon
                faces.append((a, c, b))
                faces.append((b, c, d))
        return Mesh(vertices=vertices, faces=faces)
