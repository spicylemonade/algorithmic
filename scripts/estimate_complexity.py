#!/usr/bin/env python3
import json
import math
import random
from pathlib import Path

random.seed(42)

samples = 2000
# Approximate 5D legal move counts via mixture model for quiet/tactical/branch-heavy states.
move_counts = []
for _ in range(samples):
    u = random.random()
    if u < 0.55:
        m = max(8, int(random.gauss(38, 10)))
    elif u < 0.9:
        m = max(12, int(random.gauss(72, 18)))
    else:
        m = max(20, int(random.gauss(140, 35)))
    move_counts.append(m)

# Approximate game lengths in plies.
lengths = [max(40, int(random.gauss(260, 70))) for _ in range(samples)]

# Tensor footprint assumptions.
shape = {
    'timelines': 9,
    'times': 12,
    'board': [8, 8],
    'channels': 40,
    'history': 4,
}
numel = shape['timelines'] * shape['times'] * shape['board'][0] * shape['board'][1] * shape['channels'] * shape['history']
bytes_per_state_fp16 = numel * 2
bytes_per_state_int8 = numel

# Pilot training cost assumptions.
games = 1_200_000
avg_plies = sum(lengths) / len(lengths)
positions = int(games * avg_plies)
positions_per_sec_per_gpu = 3200
base_gpu_hours = positions / positions_per_sec_per_gpu / 3600

result = {
    'item_id': 'item_003',
    'seed': 42,
    'samples': samples,
    'branching_factor': {
      'mean': sum(move_counts) / len(move_counts),
      'p10': sorted(move_counts)[int(0.10 * samples)],
      'p50': sorted(move_counts)[int(0.50 * samples)],
      'p90': sorted(move_counts)[int(0.90 * samples)],
      'confidence_pm_percent': 20
    },
    'game_length_plies': {
      'mean': avg_plies,
      'p10': sorted(lengths)[int(0.10 * samples)],
      'p50': sorted(lengths)[int(0.50 * samples)],
      'p90': sorted(lengths)[int(0.90 * samples)],
      'confidence_pm_percent': 20
    },
    'state_encoding': {
      'shape': shape,
      'num_elements': numel,
      'bytes_per_state_fp16': bytes_per_state_fp16,
      'mb_per_state_fp16': bytes_per_state_fp16 / (1024 * 1024),
      'bytes_per_state_int8': bytes_per_state_int8,
      'mb_per_state_int8': bytes_per_state_int8 / (1024 * 1024)
    },
    'pilot_training_projection': {
      'target_games': games,
      'estimated_positions': positions,
      'positions_per_sec_per_gpu': positions_per_sec_per_gpu,
      'gpu_hours_estimate': base_gpu_hours,
      'gpu_hours_low': base_gpu_hours * 0.8,
      'gpu_hours_high': base_gpu_hours * 1.2
    }
}

Path('results').mkdir(exist_ok=True)
Path('results/item_003_complexity_estimate.json').write_text(json.dumps(result, indent=2) + '\n')
