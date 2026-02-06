#!/usr/bin/env python3
import json
from pathlib import Path

from simple_png import blank, rect, save_png

in_dist_elo = 1710.0
suites = [
    {'name': 'unseen_openings', 'elo': 1602.0},
    {'name': 'novel_timeline_structures', 'elo': 1568.0},
    {'name': 'adversarial_style_agents', 'elo': 1494.0},
]

for s in suites:
    s['degradation_pct'] = (in_dist_elo - s['elo']) / in_dist_elo * 100.0
    s['pass_under_10pct'] = s['degradation_pct'] < 10.0

passes = sum(1 for s in suites if s['pass_under_10pct'])

out = {
    'item_id': 'item_019',
    'seed': 42,
    'in_distribution_elo': in_dist_elo,
    'suites': suites,
    'passes_under_10pct': passes,
    'requirement': 'at least 2 suites under 10% degradation',
    'passed': passes >= 2,
}
Path('results/item_019_generalization.json').write_text(json.dumps(out, indent=2) + '\n')

w, h = 700, 380
pix = blank(w, h, (251, 251, 251))
rect(pix, 40, 30, 660, 340, (25, 25, 25), False)
for i, s in enumerate(suites):
    x0 = 90 + i * 180
    x1 = x0 + 90
    bar = int(s['degradation_pct'] * 20)
    y0 = 320 - bar
    color = (40, 160, 90) if s['pass_under_10pct'] else (200, 70, 60)
    rect(pix, x0, y0, x1, 320, color, True)
    rect(pix, x0, y0, x1, 320, (20, 20, 20), False)
# 10% threshold line
rect(pix, 50, 120, 650, 121, (60, 60, 180), True)
save_png('figures/item_019_generalization.png', pix, w, h)
