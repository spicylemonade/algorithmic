"""SAGE-style non-convex evolutionary refinement."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .geometry import Mesh
from .convex_solver import _build_scaled_mesh, _loss


@dataclass
class EvoState:
    radii: List[float]
    period: float
    loss: float
    generations: int


def _mutate(radii: List[float], sigma: float, p: float) -> List[float]:
    out = radii[:]
    for i in range(len(out)):
        if random.random() < p:
            out[i] = max(0.25, min(2.0, out[i] + random.gauss(0.0, sigma)))
    return out


def _crossover(a: List[float], b: List[float]) -> List[float]:
    return [ai if random.random() < 0.5 else bi for ai, bi in zip(a, b)]


def refine_nonconvex(template: Mesh, obs: Sequence[Dict[str, float]], init_radii: Sequence[float], init_period: float, seed: int = 42, generations: int = 120, pop_size: int = 60) -> EvoState:
    random.seed(seed)
    pop: List[Tuple[List[float], float]] = []
    for _ in range(pop_size):
        r = [max(0.25, min(2.0, x + random.gauss(0.0, 0.05))) for x in init_radii]
        p = max(0.1, init_period + random.gauss(0.0, 0.02))
        pop.append((r, p))

    best = EvoState(list(init_radii), init_period, float("inf"), 0)
    stale = 0

    for g in range(generations):
        scored = []
        for r, p in pop:
            l = _loss(_build_scaled_mesh(template, r), obs, p, w_smooth=0.005)
            scored.append((l, r, p))
        scored.sort(key=lambda x: x[0])

        if scored[0][0] < best.loss - 1e-6:
            best = EvoState(scored[0][1][:], scored[0][2], scored[0][0], g + 1)
            stale = 0
        else:
            stale += 1

        elite_n = max(2, int(0.1 * pop_size))
        elite = scored[:elite_n]
        next_pop: List[Tuple[List[float], float]] = [(r[:], p) for _, r, p in elite]

        while len(next_pop) < pop_size:
            _, r1, p1 = random.choice(elite)
            _, r2, p2 = random.choice(elite)
            c = _crossover(r1, r2)
            c = _mutate(c, sigma=0.04, p=0.08)
            p = max(0.1, (p1 + p2) / 2.0 + random.gauss(0.0, 0.01))
            next_pop.append((c, p))

        pop = next_pop
        if stale >= 20:
            break

    return best
