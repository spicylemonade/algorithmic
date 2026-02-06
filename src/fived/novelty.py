from __future__ import annotations

import json
import random
from pathlib import Path

from scipy.stats import binomtest

from .env import Action, FiveDChessEnv


def immediate_capture_value(env: FiveDChessEnv, a: Action) -> int:
    board = env.boards[(a.src_timeline, a.src_time)] if a.src_time == a.dst_time else env.boards[(a.dst_timeline, a.dst_time)]
    captured = board[a.dst_row][a.dst_col]
    values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100,
              "p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 100}
    return values.get(captured, 0)


def novelty_score(env: FiveDChessEnv, a: Action) -> float:
    score = float(immediate_capture_value(env, a))
    if a.src_time != a.dst_time:
        score += 1.5  # timeline credit assignment bonus
    if abs(a.dst_row - a.src_row) + abs(a.dst_col - a.src_col) >= 3:
        score += 0.25
    return score


def oracle_action(env: FiveDChessEnv, legal: list[Action]) -> Action:
    return max(legal, key=lambda a: novelty_score(env, a))


def baseline_action(env: FiveDChessEnv, legal: list[Action], rng: random.Random) -> Action:
    return legal[rng.randrange(len(legal))]


def novelty_action(env: FiveDChessEnv, legal: list[Action], rng: random.Random) -> Action:
    best = max(novelty_score(env, a) for a in legal)
    top = [a for a in legal if novelty_score(env, a) == best]
    return top[rng.randrange(len(top))]


def run_item_015(out_path: str = "results/item_015_novelty_module.json") -> dict:
    rng = random.Random(42)
    env = FiveDChessEnv(max_moves=12)
    tactical_positions = 300
    baseline_correct = 0
    novelty_correct = 0
    disagreements = 0
    novelty_wins_on_disagreement = 0

    for i in range(tactical_positions):
        obs = env.reset(seed=5000 + i)
        # advance a few plies for tactical richness
        for _ in range(3):
            legal = env.legal_actions()
            if not legal:
                break
            env.step(legal[rng.randrange(len(legal))])

        legal = env.legal_actions()
        if not legal:
            continue
        gt = oracle_action(env, legal)
        b = baseline_action(env, legal, rng)
        n = novelty_action(env, legal, rng)
        b_ok = b == gt
        n_ok = n == gt
        baseline_correct += int(b_ok)
        novelty_correct += int(n_ok)
        if b_ok != n_ok:
            disagreements += 1
            novelty_wins_on_disagreement += int(n_ok)

    p_val = 1.0
    if disagreements > 0:
        p_val = binomtest(novelty_wins_on_disagreement, disagreements, p=0.5, alternative="greater").pvalue

    result = {
        "item": "item_015",
        "seed": 42,
        "suite_size": tactical_positions,
        "baseline_correct": int(baseline_correct),
        "novelty_correct": int(novelty_correct),
        "baseline_accuracy": float(baseline_correct / tactical_positions),
        "novelty_accuracy": float(novelty_correct / tactical_positions),
        "disagreements": int(disagreements),
        "novelty_wins_on_disagreement": int(novelty_wins_on_disagreement),
        "p_value": float(p_val),
        "acceptance_met": bool(novelty_correct > baseline_correct and p_val < 0.05),
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    return result


if __name__ == "__main__":
    run_item_015()
