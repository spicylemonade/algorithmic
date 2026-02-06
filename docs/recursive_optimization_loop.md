# Recursive Optimization Loop (Item 018)

Implemented rule:
- Compute deviation per iteration: `max(Hausdorff_norm, 1 - IoU)`.
- If deviation `> 0.05`, adjust optimizer:
  - `learning_rate *= 0.8`
  - period-grid step `*= 0.5` (floor `0.002`)
- Rerun blinded inversion.
- Stop when all targets pass `<=0.05` or when `max_iter=8` is reached.

Execution artifact:
- `results/item_018_recursive_optimization.json`
- `figures/item_018_recursive_deviation.png`
