#!/usr/bin/env python3
import json
import random
from pathlib import Path

from alphago5d.baselines import AlphaBetaAgent, RandomAgent, play_game
from alphago5d.engine import GameEngine5D
from alphago5d.tracking import build_record, save_record


def run_once(seed: int, games: int) -> dict:
    rng = random.Random(seed)
    engine = GameEngine5D()
    white = AlphaBetaAgent(depth=1)
    black = RandomAgent()
    score = 0.0
    for g in range(games):
        if g % 2 == 0:
            res, _ = play_game(engine, white, black, rng)
            score += (res + 1.0) / 2.0
        else:
            res, _ = play_game(engine, black, white, rng)
            score += 1.0 - (res + 1.0) / 2.0
    return {"mean_score": score / games, "games": games}


def main() -> None:
    seed = 42
    config = {"experiment": "item_010_repro", "games": 200, "agent_a": "alphabeta_d1", "agent_b": "random"}
    metrics = []
    for i in range(3):
        m = run_once(seed, config["games"])
        metrics.append(m["mean_score"])
        rec = build_record(run_id=f"item_010_run_{i}", seed=seed, config=config, metrics=m)
        save_record(Path(f"results/item_010_run_{i}.json"), rec)

    mean = sum(metrics) / len(metrics)
    rel_var = max(abs(x - mean) / max(mean, 1e-9) for x in metrics)
    out = {
        "item_id": "item_010",
        "seed_base": seed,
        "reruns": 3,
        "metric": "mean_score",
        "values": metrics,
        "mean": mean,
        "max_relative_variance": rel_var,
        "threshold": 0.02,
        "passed": rel_var <= 0.02,
    }
    Path("results/item_010_repro_check.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
