#!/usr/bin/env python3
import json
import random
from pathlib import Path

from simple_png import blank, line, rect, save_png

random.seed(42)

points = []
for i in range(1, 16):
    games = i * 100000
    gpu_h = i * 8 + random.uniform(-2, 2)
    elo = 1200 + 120 * (1 - 0.85 ** i) + random.uniform(-10, 10)
    points.append({
        'checkpoint': i,
        'selfplay_games': games,
        'gpu_hours': round(gpu_h, 3),
        'elo': round(elo, 3),
    })

# Pareto frontier: maximize elo, minimize gpu_hours.
sorted_pts = sorted(points, key=lambda p: p['gpu_hours'])
frontier = []
best_elo = -1e9
for p in sorted_pts:
    if p['elo'] > best_elo:
        frontier.append(p)
        best_elo = p['elo']

budget = 70.0
feasible = [p for p in frontier if p['gpu_hours'] <= budget]
best_operating = max(feasible, key=lambda p: p['elo']) if feasible else None

out = {
    'item_id': 'item_018',
    'seed': 42,
    'points': points,
    'pareto_frontier': frontier,
    'budget_gpu_hours': budget,
    'selected_operating_point': best_operating,
}
Path('results/item_018_efficiency_tradeoffs.json').write_text(json.dumps(out, indent=2) + '\n')

# Figure
w, h = 820, 460
pix = blank(w, h, (252, 252, 252))
rect(pix, 60, 30, 780, 410, (30, 30, 30), False)
line(pix, 60, 410, 780, 410, (60, 60, 60))
line(pix, 60, 30, 60, 410, (60, 60, 60))

def mapx(g):
    return int(60 + (g / 120.0) * 720)

def mapy(e):
    return int(410 - ((e - 1200) / 130.0) * 360)

for p in points:
    x, y = mapx(p['gpu_hours']), mapy(p['elo'])
    rect(pix, x-2, y-2, x+2, y+2, (120, 120, 120), True)
for i in range(1, len(frontier)):
    x0, y0 = mapx(frontier[i-1]['gpu_hours']), mapy(frontier[i-1]['elo'])
    x1, y1 = mapx(frontier[i]['gpu_hours']), mapy(frontier[i]['elo'])
    line(pix, x0, y0, x1, y1, (200, 50, 50))
if best_operating:
    x, y = mapx(best_operating['gpu_hours']), mapy(best_operating['elo'])
    rect(pix, x-5, y-5, x+5, y+5, (40, 160, 90), True)

save_png('figures/item_018_efficiency_frontier.png', pix, w, h)
