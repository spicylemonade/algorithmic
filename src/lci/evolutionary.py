from dataclasses import dataclass
from typing import Callable, List
import random


@dataclass
class GAConfig:
    population_size: int = 40
    generations: int = 120
    mutation_rate: float = 0.2
    crossover_rate: float = 0.7
    elitism: int = 4
    stall_limit: int = 20
    seed: int = 42


def crossover(a: List[float], b: List[float], rng: random.Random) -> List[float]:
    cut = rng.randint(1, len(a) - 1)
    return a[:cut] + b[cut:]


def mutate(v: List[float], rng: random.Random, scale: float = 0.05) -> List[float]:
    out = list(v)
    for i in range(len(out)):
        if rng.random() < 0.2:
            out[i] += rng.uniform(-scale, scale)
    return out


def refine_nonconvex(
    convex_seed: List[float],
    objective: Callable[[List[float]], float],
    cfg: GAConfig,
) -> List[float]:
    rng = random.Random(cfg.seed)
    pop = [
        [x + rng.uniform(-0.02, 0.02) for x in convex_seed]
        for _ in range(cfg.population_size)
    ]
    best = min(pop, key=objective)
    best_score = objective(best)
    stall = 0

    for _ in range(cfg.generations):
        ranked = sorted(pop, key=objective)
        elites = ranked[: cfg.elitism]
        next_pop = elites[:]

        while len(next_pop) < cfg.population_size:
            p1 = ranked[rng.randint(0, cfg.population_size // 2)]
            p2 = ranked[rng.randint(0, cfg.population_size // 2)]
            child = p1
            if rng.random() < cfg.crossover_rate:
                child = crossover(p1, p2, rng)
            if rng.random() < cfg.mutation_rate:
                child = mutate(child, rng)
            next_pop.append(child)

        pop = next_pop
        gen_best = min(pop, key=objective)
        gen_score = objective(gen_best)
        if gen_score < best_score:
            best = gen_best
            best_score = gen_score
            stall = 0
        else:
            stall += 1
        if stall >= cfg.stall_limit:
            break
    return best
