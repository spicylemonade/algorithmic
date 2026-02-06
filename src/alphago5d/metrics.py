from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass(frozen=True)
class MetricsRecord:
    step: int
    elo: float
    win_rate: float
    node_expansions_per_sec: float
    training_throughput_samples_per_sec: float
    wall_clock_cost_usd: float
    memory_peak_mb: float


def append_metrics(path: str, record: MetricsRecord) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record), sort_keys=True) + "\n")
