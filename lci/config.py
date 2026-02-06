"""Configuration definitions for reproducible LCI runs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RunConfig:
    seed: int = 42
    convex_iters: int = 400
    evo_generations: int = 400
    sparse_min_points: int = 100
