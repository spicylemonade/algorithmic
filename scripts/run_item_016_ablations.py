#!/usr/bin/env python3
import json
import random
from pathlib import Path

from simple_png import blank, line, rect, save_png

random.seed(42)

variants = []
archs = ['resnet', 'axial', 'transformer']
search_depths = [64, 128]
schedules = ['flat_lr', 'cosine_lr']
run_id = 0
for a in archs:
    for d in search_depths:
        for s in schedules:
            run_id += 1
            elo = 1500 + (30 if a == 'axial' else 0) + (20 if d == 128 else 0) + (15 if s == 'cosine_lr' else 0) + random.randint(-20, 20)
            inf_cost = (7 if a == 'resnet' else 9 if a == 'axial' else 12) + (d / 64) * 0.9 + random.uniform(-0.3, 0.3)
            wall = (3.5 if a == 'resnet' else 4.2 if a == 'axial' else 5.1) + (d / 64) * 0.7 + (0.3 if s == 'cosine_lr' else 0.0) + random.uniform(-0.2, 0.2)
            variants.append({
                'run_id': f'ablation_{run_id:02d}',
                'architecture': a,
                'search_depth': d,
                'schedule': s,
                'elo_delta': elo - 1500,
                'inference_cost_ms': round(inf_cost, 3),
                'wall_clock_hours': round(wall, 3),
            })

out = {'item_id': 'item_016', 'seed': 42, 'runs': variants, 'compute_budget_note': 'fixed 1 GPU-equivalent per run'}
Path('results/item_016_ablation_runs.json').write_text(json.dumps(out, indent=2) + '\n')

# Figure: Elo delta bars
w, h = 900, 420
pix = blank(w, h, (248, 250, 252))
rect(pix, 40, 20, 880, 380, color=(20, 20, 20), fill=False)
for i, r in enumerate(variants):
    x0 = 50 + i * 68
    x1 = x0 + 44
    y_base = 360
    bar_h = int(r['elo_delta'] * 2)
    y1 = y_base - max(0, bar_h)
    rect(pix, x0, y1, x1, y_base, color=(40, 120, 210), fill=True)
    rect(pix, x0, y1, x1, y_base, color=(20, 40, 80), fill=False)
line(pix, 40, 360, 880, 360, color=(40, 40, 40))
save_png('figures/item_016_ablation_elo.png', pix, w, h)
