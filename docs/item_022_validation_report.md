# Validation and Convergence Report

## Metric Distributions
- Source artifacts: `results/item_017_blind_runs.json`, `results/item_018_geometry_metrics.json`
- Includes per-target runtime, convex/evolutionary loss, normalized Hausdorff, IoU, and pass/fail vs 5% threshold.

## Convergence Traces
- Evolutionary stage improved loss on most targets in blind runs.
- Convergence fraction and mean losses are summarized in `results/item_022_validation_report.json`.

## Failure Analyses
- Sparse geometry coverage drives ambiguity.
- Mesh resolution and current objective simplifications limit geometric fidelity.
- Metric proxy choices (bbox IoU) introduce approximation bias.

## Deviation Target Statement
The strict deviation objective (`<5%` for all validation targets) is **not achieved** in the current benchmark configuration.
