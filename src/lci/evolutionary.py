from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .geometry import peanut_points
from .photometry import light_curve


@dataclass
class EvoResult:
    genome: np.ndarray
    objective: float


def decode_genome(genome: np.ndarray, n_pts: int = 300) -> np.ndarray:
    a, b, c, neck = genome
    return peanut_points(float(a), float(b), float(c), neck=float(np.clip(neck, 0.0, 0.7)), n=n_pts)


def objective(genome: np.ndarray, period_h: float, times_h: np.ndarray, obs_mag: np.ndarray, sun_dir: np.ndarray, obs_dir: np.ndarray) -> float:
    pts = decode_genome(genome)
    pred = light_curve(pts, period_h, times_h, sun_dir, obs_dir)
    return float(np.mean((pred - obs_mag) ** 2))


def evolve_nonconvex(
    init_population: np.ndarray,
    period_h: float,
    times_h: np.ndarray,
    obs_mag: np.ndarray,
    sun_dir: np.ndarray,
    obs_dir: np.ndarray,
    generations: int = 25,
    elite: int = 8,
    seed: int = 42,
) -> EvoResult:
    rng = np.random.default_rng(seed)
    pop = init_population.copy()

    for _ in range(generations):
        scores = np.array([objective(g, period_h, times_h, obs_mag, sun_dir, obs_dir) for g in pop])
        idx = np.argsort(scores)
        survivors = pop[idx[:elite]]

        children = []
        while len(children) + elite < pop.shape[0]:
            p1 = survivors[rng.integers(0, elite)]
            p2 = survivors[rng.integers(0, elite)]
            alpha = rng.uniform(0.2, 0.8)
            child = alpha * p1 + (1 - alpha) * p2
            child += rng.normal(0.0, [0.03, 0.03, 0.03, 0.04], size=4)
            child[0:3] = np.clip(child[0:3], 0.5, 1.8)
            child[3] = np.clip(child[3], 0.0, 0.7)
            children.append(child)

        pop = np.vstack([survivors, np.array(children)])

    scores = np.array([objective(g, period_h, times_h, obs_mag, sun_dir, obs_dir) for g in pop])
    best = int(np.argmin(scores))
    return EvoResult(genome=pop[best], objective=float(scores[best]))
