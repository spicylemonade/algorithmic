# Novel Efficiency Methods

## Method A: Symmetry-Aware Timeline Canonical Cache

Idea:
- Canonicalize `(timeline,time,board)` slices under board symmetries and timeline relabeling before cache lookup.
- Share value/policy estimates across equivalent states.

Complexity impact:
- Baseline transposition lookup: `O(1)` hash, low hit rate.
- Canonicalized lookup: `O(k)` transform attempts (`k<=8`) then `O(1)` hash.
- Expected net gain when hit-rate increase offsets transform cost.

Comparison criteria:
- Primary: nodes/sec and Elo at fixed wall-clock.
- Secondary: cache hit rate, memory overhead, collision rate.
- Success: >=25% hit-rate increase, >=15% nodes/sec gain, non-negative Elo delta.

## Method B: Learned Move-Pruning Gate

Idea:
- Lightweight gating network predicts move retention probabilities before full expansion.
- Keep top-`k` actions (dynamic with uncertainty floor), prune low-probability branches.

Complexity impact:
- Baseline expansion: `O(B)` children.
- Gated expansion: `O(B)` scoring + `O(B log k)` select, then evaluate only `k << B`.
- Effective simulation cost scales with retained branching factor.

Comparison criteria:
- Primary: simulations/sec and Elo under equal time controls.
- Secondary: prune recall for eventual best move, calibration error.
- Success: >=35% simulations/sec gain with <=20 Elo loss (or positive Elo with longer search horizon).
