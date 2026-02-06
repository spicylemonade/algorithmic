"""Non-convex evolutionary inversion core (SAGE inspired)."""

from __future__ import annotations

import random


def _fitness(individual: dict, observations: list[dict]) -> float:
    target = sum(obs.get("flux", 1.0) for obs in observations) / max(len(observations), 1)
    return -abs(individual["flux_model"] - target)


def optimize_nonconvex(initial_population: list[dict], observations: list[dict], config) -> dict:
    rng = random.Random(getattr(config, "seed", 42))
    population_size = 96
    max_generations = getattr(config, "evo_generations", 400)
    elitism_ratio = 0.1
    restart_patience = 50
    mutation_sigma = 0.03

    if not initial_population:
        initial_population = [{"flux_model": rng.uniform(0.5, 1.5)} for _ in range(population_size)]

    population = initial_population[:population_size]
    best = None
    stale = 0

    for gen in range(1, max_generations + 1):
        scored = [(ind, _fitness(ind, observations)) for ind in population]
        scored.sort(key=lambda t: t[1], reverse=True)
        if best is None or scored[0][1] > best[1]:
            best = scored[0]
            stale = 0
        else:
            stale += 1

        elite_n = max(1, int(elitism_ratio * population_size))
        next_pop = [dict(scored[i][0]) for i in range(elite_n)]

        while len(next_pop) < population_size:
            p1 = rng.choice(scored[: max(2, population_size // 3)])[0]
            p2 = rng.choice(scored[: max(2, population_size // 3)])[0]
            child = {"flux_model": 0.5 * (p1["flux_model"] + p2["flux_model"]) + rng.gauss(0.0, mutation_sigma)}
            next_pop.append(child)

        if stale >= restart_patience:
            # Keep elites, randomize the remainder to escape local minima.
            for i in range(elite_n, population_size):
                next_pop[i]["flux_model"] = rng.uniform(0.5, 1.5)
            stale = 0

        population = next_pop

    return {
        "best": best[0] if best else None,
        "fitness": best[1] if best else float("-inf"),
        "generations": max_generations,
        "population_size": population_size,
        "elitism_ratio": elitism_ratio,
        "restart_patience": restart_patience,
    }
