from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

from .agents import HeuristicAgent, RandomAgent, ShallowSearchAgent
from .env import FiveDChessEnv


@dataclass
class BenchmarkStats:
    wins_white: int = 0
    wins_black: int = 0
    draws: int = 0
    total_branching: int = 0
    total_moves: int = 0
    total_latency_s: float = 0.0

    def to_dict(self) -> dict:
        total_games = self.wins_white + self.wins_black + self.draws
        return {
            "games": total_games,
            "white_win_rate": self.wins_white / total_games,
            "black_win_rate": self.wins_black / total_games,
            "draw_rate": self.draws / total_games,
            "avg_branching_factor": self.total_branching / max(self.total_moves, 1),
            "avg_move_latency_ms": 1000.0 * self.total_latency_s / max(self.total_moves, 1),
        }


def run_baseline(name: str, agent, games: int = 1000, seed: int = 42) -> dict:
    rng = random.Random(seed)
    stats = BenchmarkStats()
    for g in range(games):
        env = FiveDChessEnv(max_moves=12)
        env.reset(seed=seed + g)
        while not env.is_terminal():
            legal = env.legal_actions()
            if not legal:
                break
            stats.total_branching += len(legal)
            t0 = time.perf_counter()
            action = agent.select_action(env, legal, rng)
            stats.total_latency_s += time.perf_counter() - t0
            stats.total_moves += 1
            _, reward, done, _ = env.step(action)
            if done:
                if reward > 0:
                    stats.wins_white += 1
                elif reward < 0:
                    stats.wins_black += 1
                else:
                    stats.draws += 1
                break
        else:
            stats.draws += 1
    out = stats.to_dict()
    out["baseline"] = name
    out["seed"] = seed
    return out


def run_all(games: int = 1000, seed: int = 42, out_path: str = "results/item_008_baselines.json") -> dict:
    baselines = [
        ("random", RandomAgent()),
        ("heuristic", HeuristicAgent()),
        ("shallow_search", ShallowSearchAgent()),
    ]
    rows = [run_baseline(name, agent, games=games, seed=seed) for name, agent in baselines]
    result = {"item": "item_008", "seed": seed, "games_per_baseline": games, "results": rows}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    return result


if __name__ == "__main__":
    run_all()
