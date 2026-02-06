from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agents import HeuristicAgent
from .benchmark import run_baseline


@dataclass
class RunConfig:
    name: str
    seed: int
    games: int

    def config_hash(self) -> str:
        payload = json.dumps({"name": self.name, "seed": self.seed, "games": self.games}, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def get_hardware_info() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def run_tracked(config: RunConfig) -> dict:
    metrics = run_baseline("heuristic", HeuristicAgent(), games=config.games, seed=config.seed)
    return {
        "run_name": config.name,
        "git_commit": get_git_commit(),
        "config_hash": config.config_hash(),
        "seed": config.seed,
        "hardware": get_hardware_info(),
        "metrics": metrics,
    }


def relative_error(a: float, b: float) -> float:
    denom = max(abs(a), 1e-12)
    return abs(a - b) / denom


def reproducibility_report(out_path: str = "results/item_010_tracking_repro.json") -> dict:
    cfg = RunConfig(name="heuristic_repro_check", seed=42, games=600)
    r1 = run_tracked(cfg)
    r2 = run_tracked(cfg)

    # Key reproducibility metrics focus on deterministic game outcomes and search statistics.
    keys = ["white_win_rate", "black_win_rate", "draw_rate", "avg_branching_factor"]
    rel = {k: relative_error(r1["metrics"][k], r2["metrics"][k]) for k in keys}
    max_rel = max(rel.values())

    out = {
        "item": "item_010",
        "seed": 42,
        "run_1": r1,
        "run_2": r2,
        "relative_errors": rel,
        "max_relative_error": max_rel,
        "acceptance_met": max_rel <= 0.02,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    return out


if __name__ == "__main__":
    reproducibility_report()
