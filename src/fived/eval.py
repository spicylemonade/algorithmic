from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .agents import HeuristicAgent, RandomAgent, ShallowSearchAgent
from .env import FiveDChessEnv


@dataclass
class MatchSummary:
    wins_a: int = 0
    wins_b: int = 0
    draws: int = 0

    @property
    def games(self) -> int:
        return self.wins_a + self.wins_b + self.draws


def material_score(env: FiveDChessEnv) -> int:
    values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100}
    score = 0
    for board in env.boards.values():
        for row in board:
            for p in row:
                if p == ".":
                    continue
                score += values.get(p.upper(), 0) if p.isupper() else -values.get(p.upper(), 0)
    return score


def play_game(agent_w, agent_b, seed: int) -> float:
    rng = random.Random(seed)
    env = FiveDChessEnv(max_moves=14)
    env.reset(seed=seed)
    while not env.is_terminal():
        legal = env.legal_actions()
        if not legal:
            break
        actor = agent_w if env.side_to_move == "W" else agent_b
        action = actor.select_action(env, legal, rng)
        _, reward, done, _ = env.step(action)
        if done:
            if reward > 0:
                return 1.0
            if reward < 0:
                return 0.0
            break
    # Tie-break by material to reduce pathological draw-only regimes.
    m = material_score(env)
    if m > 0:
        return 1.0
    if m < 0:
        return 0.0
    return 0.5


def run_head_to_head(agent_a, agent_b, games: int = 2400, seed: int = 42) -> dict:
    summary = MatchSummary()
    for i in range(games):
        # Side balancing by swap on odd rounds.
        if i % 2 == 0:
            score_a = play_game(agent_a, agent_b, seed + i)
        else:
            score_a = 1.0 - play_game(agent_b, agent_a, seed + i)
        if score_a == 1.0:
            summary.wins_a += 1
        elif score_a == 0.0:
            summary.wins_b += 1
        else:
            summary.draws += 1

    p = (summary.wins_a + 0.5 * summary.draws) / summary.games
    p = min(max(p, 1e-6), 1 - 1e-6)
    elo = 400.0 * math.log10(p / (1 - p))
    se = math.sqrt(p * (1 - p) / summary.games)
    lo_p = min(max(p - 1.96 * se, 1e-6), 1 - 1e-6)
    hi_p = min(max(p + 1.96 * se, 1e-6), 1 - 1e-6)
    lo_elo = 400.0 * math.log10(lo_p / (1 - lo_p))
    hi_elo = 400.0 * math.log10(hi_p / (1 - hi_p))
    return {
        "games": summary.games,
        "wins_a": summary.wins_a,
        "wins_b": summary.wins_b,
        "draws": summary.draws,
        "score_a": p,
        "elo_a_minus_b": elo,
        "elo_ci95": [lo_elo, hi_elo],
        "elo_ci95_width": hi_elo - lo_elo,
    }


def run_round_robin(agents: Dict[str, object], games_per_pair: int = 300, seed: int = 42) -> dict:
    names = list(agents.keys())
    table = {}
    idx = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            table[f"{a}_vs_{b}"] = run_head_to_head(agents[a], agents[b], games=games_per_pair, seed=seed + idx)
            idx += games_per_pair
    return table


def run_eval_pipeline(out_path: str = "results/item_009_evaluation_pipeline.json") -> dict:
    agents = {
        "random": RandomAgent(),
        "heuristic": HeuristicAgent(),
        "shallow": ShallowSearchAgent(),
    }
    h2h = run_head_to_head(agents["heuristic"], agents["random"], games=5000, seed=42)
    rr = run_round_robin(agents, games_per_pair=300, seed=4242)
    result = {
        "item": "item_009",
        "seed": 42,
        "head_to_head": h2h,
        "round_robin": rr,
        "acceptance_met": h2h["elo_ci95_width"] <= 80.0,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    return result


if __name__ == "__main__":
    run_eval_pipeline()
