from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Observation:
    jd: float
    mag: float
    sigma: float
    phase_angle_deg: float
    source: str


@dataclass
class SpinState:
    lambda_deg: float
    beta_deg: float
    period_hours: float
    phi0_deg: float


@dataclass
class Mesh:
    vertices: List[List[float]]
    faces: List[List[int]]


@dataclass
class InversionResult:
    asteroid_id: str
    mesh: Mesh
    spin: SpinState
    metrics: Dict[str, float]
