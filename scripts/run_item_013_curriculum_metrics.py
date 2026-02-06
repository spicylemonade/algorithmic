#!/usr/bin/env python3
import json
from pathlib import Path

out = {
    "item_id": "item_013",
    "seed": 42,
    "temperature_schedule": [
        {"games": [0, 200000], "tau": 1.0},
        {"games": [200001, 800000], "tau": 0.5},
        {"games": [800001, 999999999], "tau": 0.1}
    ],
    "resignation_policy": {
        "enabled_after_games": 150000,
        "value_threshold": -0.92,
        "verification_rate": 0.1
    },
    "replay_buffer": {
        "window_games": 500000,
        "sampling_weights": {
            "recent": 0.55,
            "mid": 0.30,
            "old": 0.15
        },
        "dedupe_policy": "state-hash dedupe within minibatch"
    },
    "target_generation_rate_games_per_hour": 25000,
    "buffer_diversity_targets": {
        "opening_entropy_min_bits": 4.0,
        "timeline_branch_histogram_jsd_max": 0.18,
        "unique_state_hash_ratio_min": 0.72
    }
}
Path('results/item_013_curriculum_metrics.json').write_text(json.dumps(out, indent=2) + '\n')
