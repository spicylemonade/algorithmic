#!/usr/bin/env python3
import json
import math
from pathlib import Path

# Two-proportion sample size approximation for win-rate difference.
# Target: 95% confidence (alpha=0.05), 80% power.
alpha_z = 1.96
power_z = 0.84
p1 = 0.50
p2 = 0.55  # Detect 5-point absolute win-rate improvement.
p_bar = 0.5 * (p1 + p2)
num = (alpha_z * math.sqrt(2 * p_bar * (1 - p_bar)) + power_z * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
den = (p2 - p1) ** 2
n_per_group = math.ceil(num / den)

out = {
    "item_id": "item_009",
    "seed": 42,
    "alpha": 0.05,
    "confidence": 0.95,
    "power": 0.80,
    "detectable_winrate_delta": p2 - p1,
    "required_games_per_group": n_per_group,
    "required_total_games_head_to_head": 2 * n_per_group,
}
Path("results/item_009_power_analysis.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
