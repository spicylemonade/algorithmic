# Compute-Efficiency Strategy

## Tactics
- Mixed precision (`fp16/bf16`) for model forward/backward.
- Inference batching across MCTS roots and self-play workers.
- Policy/value cache keyed by state hash + model version.
- Parallel actor-learner topology with queue-based decoupling.
- Prefetching and pinned-memory pipelines for replay batches.

## Targeted Impact
- Mixed precision: 22% cost reduction.
- Batching: 18% cost reduction.
- Caching: 12% cost reduction.
- Parallelization overlap: 9% cost reduction.
- Combined conservative net reduction after overlap penalties: **36%** training cost per Elo point.

## KPI
- Baseline: `1.00 GPU-hour / +10 Elo`
- Target optimized: `<= 0.64 GPU-hour / +10 Elo`
