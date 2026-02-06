from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Geometry:
    sun_vec: Tuple[float, float, float]
    obs_vec: Tuple[float, float, float]
    phase_angle_deg: float


@dataclass
class Observation:
    jd_tdb: float
    magnitude: float
    sigma: float
    geometry: Geometry
    filter_band: str


@dataclass
class Mesh:
    vertices: List[Tuple[float, float, float]]
    faces: List[Tuple[int, int, int]]


@dataclass
class ConvexParams:
    period_hr: float
    pole_lambda_deg: float
    pole_beta_deg: float
    phase0_rad: float
    shape_coeffs: List[float]
    scatter_coeffs: List[float]
