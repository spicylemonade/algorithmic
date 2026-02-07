from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

from .types import Mesh, SpinState


@dataclass
class GeometryModule:
    n_lat: int = 12
    n_lon: int = 24

    def ellipsoid_mesh(self, a: float, b: float, c: float) -> Mesh:
        vertices: List[List[float]] = []
        faces: List[List[int]] = []
        for i in range(self.n_lat + 1):
            th = math.pi * i / self.n_lat
            for j in range(self.n_lon):
                ph = 2.0 * math.pi * j / self.n_lon
                x = a * math.sin(th) * math.cos(ph)
                y = b * math.sin(th) * math.sin(ph)
                z = c * math.cos(th)
                vertices.append([x, y, z])
        for i in range(self.n_lat):
            for j in range(self.n_lon):
                i0 = i * self.n_lon + j
                i1 = i * self.n_lon + (j + 1) % self.n_lon
                i2 = (i + 1) * self.n_lon + j
                i3 = (i + 1) * self.n_lon + (j + 1) % self.n_lon
                faces.append([i0, i2, i1])
                faces.append([i1, i2, i3])
        return Mesh(vertices=vertices, faces=faces)

    def rotation_phase(self, jd: float, spin: SpinState, jd_ref: float) -> float:
        return spin.phi0_deg + 360.0 * (jd - jd_ref) / (spin.period_hours / 24.0)
