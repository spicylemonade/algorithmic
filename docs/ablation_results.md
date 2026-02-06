# Controlled Ablation Results

Ablated model played against full model; negative Elo implies degradation.

| Ablation | Games | Win rate (ablated) | Elo delta vs full | 95% CI |
|---|---:|---:|---:|---:|
| remove_progressive_widening | 2000 | 0.405 | -66.8 | [-82.5, -51.4] |
| remove_legality_masking | 2000 | 0.380 | -85.4 | [-101.3, -69.9] |
| remove_transposition_cache | 2000 | 0.447 | -37.0 | [-52.4, -21.7] |
| remove_curriculum_schedule | 2000 | 0.448 | -36.6 | [-52.0, -21.4] |
