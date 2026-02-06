# Baseline Comparison and Ablations

## External Baselines
Direct execution of MPO LCInvert, SAGE, and KOALA was not feasible in this environment; comparison uses published methodological characteristics and reported behavior.

| Method | Comparison mode | Sparse-data handling | Non-convex support | Reference |
|---|---|---|---|---|
| MPO LCInvert | Published/tool documentation | Limited dedicated sparse inversion controls | No | MPO Canopus LCInvert docs |
| SAGE | Published benchmark | Supports sparse+dense with cadence sensitivity | Yes | Bartczak & Dudzinski 2018, DOI `10.1051/0004-6361/201731497` |
| KOALA | Published benchmark | Strong in multimodal datasets, less sparse-only focused | Partial/multimodal | KOALA literature |
| Custom LCI (this repo) | Direct run | Explicit sparse multiresolution module | Yes | This benchmark (`item_018`) |

## Ablations (>=4)
Ablation variants in `results/item_019_comparison_and_ablations.json`:
1. `convex_only`
2. `no_sparse_multiresolution`
3. `no_adaptive_reinforcement`
4. `no_physical_priors`
5. `full_hybrid_sparse_adaptive` (reference)

Observed trend: removing any novel component increases geometric deviation, with largest regression for removing non-convex refinement.
