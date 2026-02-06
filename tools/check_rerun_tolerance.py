#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.lci.pipeline import run_pilot


def rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), 1e-12)


def main() -> None:
    r1 = run_pilot(seed=42)
    r2 = run_pilot(seed=42)
    variance = {
        'period_evo': rel(r1.period_evo, r2.period_evo),
        'loss_evo': rel(r1.loss_evo, r2.loss_evo),
    }
    out = {
        'seed': 42,
        'run_1': r1.__dict__,
        'run_2': r2.__dict__,
        'relative_variance': variance,
        'within_tolerance': all(v <= 0.01 for v in variance.values()),
    }
    with open('results/item_024_rerun_check.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)


if __name__ == '__main__':
    main()
