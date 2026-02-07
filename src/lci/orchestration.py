from __future__ import annotations

from dataclasses import dataclass

from .convex_solver import ConvexSolver
from .evolutionary_solver import EvolutionarySolver
from .sparse_solver import SparseSolver
from .types import InversionResult, Observation


@dataclass
class LCIPipeline:
    seed: int = 42

    def solve_dense(self, asteroid_id: str, observations: list[Observation]) -> InversionResult:
        convex = ConvexSolver()
        evo = EvolutionarySolver(seed=self.seed)
        base = convex.solve(asteroid_id, observations)
        return evo.refine(base, observations)

    def solve_sparse(self, asteroid_id: str, observations: list[Observation]) -> InversionResult:
        sparse = SparseSolver()
        return sparse.solve_sparse(asteroid_id, observations)
