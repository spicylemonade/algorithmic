from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Candidate:
    object_id: str
    is_neo: bool
    diameter_km: float
    lcdb_u: float
    in_damit: bool
    n_lightcurves: int
    n_sparse_points: int
    n_apparitions: int


def evaluate_rules(c: Candidate) -> dict:
    r1 = c.is_neo or (c.diameter_km > 100.0)
    r2 = c.lcdb_u >= 2.0
    r3 = not c.in_damit
    r4 = (c.n_lightcurves > 20) or ((c.n_sparse_points > 100) and (c.n_apparitions > 3))
    return {
        "priority_1": bool(r1),
        "priority_2": bool(r2),
        "priority_3": bool(r3),
        "priority_4": bool(r4),
        "passes_all": bool(r1 and r2 and r3 and r4),
    }
