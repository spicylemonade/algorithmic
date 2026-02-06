#!/usr/bin/env python3
import itertools
import json
import math
import random
from pathlib import Path

from alphago5d.baselines import AlphaBetaAgent, MCTSAgent, RandomAgent, play_game
from alphago5d.engine import GameEngine5D


def elo_from_score(score: float) -> float:
    # Invert logistic expected score to Elo delta.
    eps = 1e-6
    s = min(max(score, eps), 1 - eps)
    return -400.0 * math.log10((1.0 / s) - 1.0)


def main() -> None:
    rng = random.Random(42)
    engine = GameEngine5D()
    agents = {
        "random": RandomAgent(),
        "alphabeta": AlphaBetaAgent(depth=1),
        "mcts": MCTSAgent(simulations=6),
    }
    pairings = [("random", "alphabeta"), ("random", "mcts"), ("alphabeta", "mcts")]

    games_total = 1000
    base = games_total // len(pairings)
    extras = games_total % len(pairings)
    records = []
    score_totals = {k: 0.0 for k in agents}
    score_games = {k: 0 for k in agents}
    node_totals = {k: 0 for k in agents}
    time_totals = {k: 0.0 for k in agents}

    for pair_idx, (a, b) in enumerate(pairings):
        wins_a = wins_b = draws = 0
        n_games = base + (1 if pair_idx < extras else 0)
        for g in range(n_games):
            if g % 2 == 0:
                res, stats = play_game(engine, agents[a], agents[b], rng)
                score_a = (res + 1.0) / 2.0
                score_b = 1.0 - score_a
            else:
                res, stats = play_game(engine, agents[b], agents[a], rng)
                score_b = (res + 1.0) / 2.0
                score_a = 1.0 - score_b
            if score_a == 1.0:
                wins_a += 1
            elif score_b == 1.0:
                wins_b += 1
            else:
                draws += 1

            score_totals[a] += score_a
            score_totals[b] += score_b
            score_games[a] += 1
            score_games[b] += 1
            for name, st in stats.items():
                node_totals[name] += st.nodes
                time_totals[name] += st.elapsed

        avg_score_a = (wins_a + 0.5 * draws) / n_games
        records.append(
            {
                "pair": [a, b],
                "games": n_games,
                "wins": {a: wins_a, b: wins_b},
                "draws": draws,
                "score": {a: avg_score_a, b: 1.0 - avg_score_a},
                "elo_delta": {a: elo_from_score(avg_score_a), b: -elo_from_score(avg_score_a)},
            }
        )

    ratings = {}
    for name in agents:
        mean_score = score_totals[name] / max(1, score_games[name])
        ratings[name] = {
            "mean_score": mean_score,
            "elo_vs_50pct": elo_from_score(mean_score),
            "nodes_per_sec": node_totals[name] / max(time_totals[name], 1e-9),
            "games": score_games[name],
        }

    out = {
        "item_id": "item_008",
        "seed": 42,
        "games_total": games_total,
        "pairwise_results": records,
        "agent_metrics": ratings,
    }

    Path("results").mkdir(exist_ok=True)
    Path("results/item_008_baseline_benchmarks.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
