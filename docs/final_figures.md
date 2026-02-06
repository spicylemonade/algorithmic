# Final Figures and Tables (Publication Set)

1. `figures/item_016_ablation_elo.png`
- Caption: Elo deltas across 12 architecture/search/schedule ablations.
- Statistical note: compare with run-level variance in `results/item_016_ablation_runs.json`.

2. `figures/item_017_elo_vs_opponents.png`
- Caption: Elo outcomes versus baseline opponents (medium time control).
- Statistical note: 95% confidence intervals reported in `results/item_017_rated_benchmark.json`.

3. `figures/item_018_efficiency_frontier.png`
- Caption: Pareto frontier of Elo versus compute.
- Statistical note: budget-constrained point selected at 70 GPU-hours.

4. `figures/item_019_generalization.png`
- Caption: Relative degradation on held-out scenario suites.
- Statistical note: threshold line indicates 10% degradation target.

5. `figures/item_020_error_taxonomy.png`
- Caption: Root-cause distribution from 200 annotated loss/draw positions.
- Statistical note: category counts from `results/item_020_error_analysis.json`.

6. `figures/item_024_learning_curve_proxy.png`
- Caption: Final learning progress proxy across training checkpoints.
- Statistical note: monotonic trend interpreted with ablation uncertainty.

7. `figures/item_024_ablation_costs.png`
- Caption: Inference-cost comparison for ablation runs.
- Statistical note: cost values reported as milliseconds per inference.

8. `figures/item_024_generalization_drop.png`
- Caption: Held-out suite degradation percentages.
- Statistical note: pass/fail criterion at <10% on at least two suites.

9. `figures/item_024_error_category_share.png`
- Caption: Error category prevalence ranking.
- Statistical note: top-3 categories selected for remediation experiments.

10. `figures/item_024_repro_variance.png`
- Caption: Relative variance across reproducibility reruns.
- Statistical note: all reruns fall below the 5% reproducibility threshold.

Tables:
- `results/item_016_ablation_runs.json`
- `results/item_017_rated_benchmark.json`
