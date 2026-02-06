#!/usr/bin/env python3
import json
import random
from pathlib import Path

from alphago5d.safety import (
    SafetyThresholds,
    detect_replay_mode_collapse,
    detect_resign_exploit,
    detect_training_collapse,
    detect_value_head_saturation,
)


def first_trigger(values, fn):
    for step, v in enumerate(values, start=1):
        if fn(v):
            return step
    return None


def main() -> None:
    rng = random.Random(42)
    th = SafetyThresholds()

    modes = {}

    entropy_series = [max(0.05, 0.9 - 0.015 * i + rng.uniform(-0.02, 0.02)) for i in range(1, 101)]
    modes["policy_collapse"] = first_trigger(entropy_series, lambda x: detect_training_collapse(x, th))

    resign_series = [min(0.99, 0.25 + 0.012 * i + rng.uniform(-0.015, 0.015)) for i in range(1, 101)]
    modes["resign_exploit_loop"] = first_trigger(resign_series, lambda x: detect_resign_exploit(x, th))

    value_std_series = [max(0.0, 0.22 - 0.004 * i + rng.uniform(-0.01, 0.01)) for i in range(1, 101)]
    modes["value_head_saturation"] = first_trigger(value_std_series, lambda x: detect_value_head_saturation(x, th))

    unique_ratio_series = [max(0.2, 0.88 - 0.007 * i + rng.uniform(-0.01, 0.01)) for i in range(1, 101)]
    modes["replay_mode_collapse"] = first_trigger(unique_ratio_series, lambda x: detect_replay_mode_collapse(x, th))

    passed = all(v is not None and v <= 50 for v in modes.values())

    out = {
        "item_id": "item_015",
        "seed": 42,
        "thresholds": th.__dict__,
        "failure_modes": [{"name": k, "detector_trigger_step": v} for k, v in modes.items()],
        "trigger_requirement_max_step": 50,
        "passed": passed,
        "rollback_strategy": {
            "checkpoint_rewind_steps": 2000,
            "optimizer_lr_backoff": 0.5,
            "replay_reset_fraction": 0.3
        }
    }
    Path('results/item_015_safety_simulation.json').write_text(json.dumps(out, indent=2) + '\n')
    assert passed, out
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
