# Sparse-First Pole Search Strategy

Method:
1. Coarse pole grid at 20 deg spacing with period scan step 0.1 h.
2. Refinement levels at 10 deg / 0.02 h, 5 deg / 0.005 h, and 2 deg / 0.001 h around top candidate.
3. Mirror-pole ambiguity pruning compares `(lambda,beta)` to `(lambda+180,-beta)`; keep both when score gap `<0.015`.

Validation:
- Executed sparse-only synthetic cases (3 total) with deterministic seed 42.
- Output stored in `results/item_012_sparse_pole_search.json`.
