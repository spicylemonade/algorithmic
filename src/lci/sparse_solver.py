from __future__ import annotations

from dataclasses import dataclass

from .convex_solver import ConvexSolver
from .types import InversionResult, Observation


@dataclass
class SparseSolver:
    min_points: int = 100

    def solve_sparse(self, asteroid_id: str, observations: list[Observation]) -> InversionResult:
        if len(observations) < self.min_points:
            raise ValueError(f"Sparse mode requires at least {self.min_points} points")
        solver = ConvexSolver(step_size=0.08, max_iter=200)
        return solver.solve(asteroid_id=asteroid_id, observations=observations)
