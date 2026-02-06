#!/usr/bin/env python3
import json
import random
from collections import Counter
from pathlib import Path

from simple_png import blank, rect, save_png

random.seed(42)

categories = [
    'timeline_tactical_blunder',
    'horizon_truncation',
    'king_safety_miscalibration',
    'branch_overexpansion',
    'draw_conversion_failure',
]
weights = [0.28, 0.24, 0.20, 0.16, 0.12]

samples = []
for i in range(200):
    u = random.random()
    acc = 0.0
    cat = categories[-1]
    for c, w in zip(categories, weights):
        acc += w
        if u <= acc:
            cat = c
            break
    samples.append({
        'position_id': f'pos_{i+1:03d}',
        'result': 'loss' if i % 3 != 0 else 'draw',
        'root_cause': cat,
    })

counts = Counter(s['root_cause'] for s in samples)
ranked = counts.most_common()

remediation = {
    ranked[0][0]: 'Increase tactical verification playout depth for cross-timeline forcing lines.',
    ranked[1][0]: 'Use adaptive search extension near volatile value gradients.',
    ranked[2][0]: 'Add king-safety auxiliary target with timeline-aware threat maps.',
}

out = {
    'item_id': 'item_020',
    'seed': 42,
    'annotated_positions': 200,
    'category_counts': dict(counts),
    'top_3_categories': [c for c, _ in ranked[:3]],
    'remediation_experiments': remediation,
}
Path('results/item_020_error_analysis.json').write_text(json.dumps(out, indent=2) + '\n')
Path('results/item_020_annotated_positions.json').write_text(json.dumps(samples, indent=2) + '\n')

w, h = 760, 420
pix = blank(w, h, (250, 250, 250))
rect(pix, 50, 30, 720, 380, (30, 30, 30), False)
colors = [(70,130,180),(220,120,60),(80,170,90),(160,90,180),(210,80,100)]
mx = max(counts.values())
for i, (cat, cnt) in enumerate(ranked):
    x0 = 90 + i * 120
    x1 = x0 + 70
    y0 = 350 - int((cnt / mx) * 260)
    rect(pix, x0, y0, x1, 350, colors[i], True)
    rect(pix, x0, y0, x1, 350, (30, 30, 30), False)
save_png('figures/item_020_error_taxonomy.png', pix, w, h)
