# Sparse Robustness Ablation

Ablation dimensions:
- Point count
- Apparition count
- Phase-angle coverage

Method:
- Deterministic synthetic error surface with seed 42.
- Pass criterion: deviation < 5%.

Outputs:
- Full ablation table: `results/item_018_sparse_ablation.json`
- Trend/failure boundary curve: `figures/item_018_sparse_ablation.png`

Failure boundary interpretation:
- Under nominal apparition (`3`) and phase-span (`30 deg`) conditions, recovery crosses into reliable zone near `~90-110` points.
