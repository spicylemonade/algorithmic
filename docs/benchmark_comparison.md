# Benchmark Comparison vs Existing Tools

## Executed
- Computed custom pipeline metrics on the shared 10-target blind-validation set.
- Aggregated per-target and mean performance in `results/item_017_benchmark_comparison_partial.json`.

## Blocker
Exact acceptance requires metric deltas against MPO LCInvert, SAGE, and KOALA on *identical* data partitions. This could not be completed in this environment because:
- MPO LCInvert and KOALA are not available as runnable binaries/APIs here.
- No standardized automated benchmark harness for all three tools with identical partitions was available in-session.

## Outcome
This item is marked failed with partial output preserved for reproducibility.
