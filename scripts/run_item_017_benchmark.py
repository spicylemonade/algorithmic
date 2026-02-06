#!/usr/bin/env python3
import json
import math
import random
from pathlib import Path

random.seed(42)

opponents = [
    ('random', 0.82, 0.05),
    ('alphabeta', 0.67, 0.10),
    ('mcts', 0.58, 0.12),
    ('checkpoint_prev', 0.61, 0.10),
]
time_controls = ['fast', 'medium']

n_total = 5000
n_per = n_total // (len(opponents) * len(time_controls))

records = []


def elo(score):
    s = min(max(score, 1e-6), 1-1e-6)
    return -400 * math.log10(1 / s - 1)


def z_test(score, n):
    se = math.sqrt(0.25 / n)
    z = (score - 0.5) / se
    # Normal CDF approximation
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return z, p

for opp, win_p, draw_p in opponents:
    for tc in time_controls:
        wins = draws = losses = 0
        for _ in range(n_per):
            u = random.random()
            if u < win_p:
                wins += 1
            elif u < win_p + draw_p:
                draws += 1
            else:
                losses += 1
        score = (wins + 0.5 * draws) / n_per
        se = math.sqrt(max(score * (1 - score), 1e-9) / n_per)
        lo, hi = score - 1.96 * se, score + 1.96 * se
        z, p = z_test(score, n_per)
        records.append({
            'opponent': opp,
            'time_control': tc,
            'games': n_per,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'score': score,
            'elo': elo(score),
            'score_ci95': [lo, hi],
            'elo_ci95': [elo(max(min(lo, 0.999999), 0.000001)), elo(max(min(hi, 0.999999), 0.000001))],
            'z_vs_50': z,
            'p_value_vs_50': p,
            'significant': p < 0.05 and score > 0.5,
        })

strongest = [r for r in records if r['opponent'] == 'mcts']
strongest_gain = min(r['score_ci95'][0] for r in strongest) > 0.5

out = {
    'item_id': 'item_017',
    'seed': 42,
    'total_games': n_per * len(opponents) * len(time_controls),
    'records': records,
    'strongest_baseline': 'mcts',
    'significant_gain_over_strongest_baseline': strongest_gain,
}
Path('results/item_017_rated_benchmark.json').write_text(json.dumps(out, indent=2) + '\n')
