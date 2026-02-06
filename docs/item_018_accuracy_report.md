# Geometric Reconstruction Accuracy

Computed for each validation target:
- normalized Hausdorff distance
- volumetric IoU proxy
- deviation criterion `max(normalized_hausdorff, 1-IoU)`
- pass/fail against 5% threshold

See `results/item_018_geometry_metrics.json` for per-target and summary statistics (mean/median/worst-case).
