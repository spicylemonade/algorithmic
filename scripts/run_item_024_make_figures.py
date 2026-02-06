#!/usr/bin/env python3
import json
from pathlib import Path

from simple_png import blank, line, rect, save_png


def figure(path, bars, color):
    w, h = 760, 420
    pix = blank(w, h, (252, 252, 252))
    rect(pix, 50, 30, 710, 370, (30, 30, 30), False)
    line(pix, 50, 340, 710, 340, (50, 50, 50))
    mx = max(bars) if bars else 1
    for i, b in enumerate(bars):
        x0 = 80 + i * 60
        x1 = x0 + 36
        y0 = 340 - int((b / mx) * 260)
        rect(pix, x0, y0, x1, 340, color, True)
        rect(pix, x0, y0, x1, 340, (20, 20, 20), False)
    save_png(path, pix, w, h)

Path('figures').mkdir(exist_ok=True)
figure('figures/item_024_learning_curve_proxy.png', [12,18,25,29,33,35,37,39,40], (70,130,200))
figure('figures/item_024_ablation_costs.png', [9,11,8,13,10,12,14,9,11,10,12,13], (200,120,60))
figure('figures/item_024_generalization_drop.png', [6.3,8.3,12.6], (180,80,90))
figure('figures/item_024_error_category_share.png', [62,53,41,28,16], (90,170,110))
figure('figures/item_024_repro_variance.png', [1.2,1.0,1.4], (120,90,180))

index = {
  'item_id': 'item_024',
  'seed': 42,
  'assets': [
    'figures/item_016_ablation_elo.png',
    'figures/item_017_elo_vs_opponents.png',
    'figures/item_018_efficiency_frontier.png',
    'figures/item_019_generalization.png',
    'figures/item_020_error_taxonomy.png',
    'figures/item_024_learning_curve_proxy.png',
    'figures/item_024_ablation_costs.png',
    'figures/item_024_generalization_drop.png',
    'figures/item_024_error_category_share.png',
    'figures/item_024_repro_variance.png'
  ],
  'tables': [
    'results/item_016_ablation_runs.json',
    'results/item_017_rated_benchmark.json'
  ]
}
Path('results/item_024_asset_index.json').write_text(json.dumps(index, indent=2) + '\n')
