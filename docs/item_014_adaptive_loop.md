# Adaptive Loss Weighting and Self-Reinforcement

Implemented in `src/lci/reinforcement.py`.

Logic:
- If validation deviation `> 5%`, update loss weights (`w_sparse`, `w_phys`) and tighten period granularity.
- Retry capped by `max_retries` (default `5`).
- Rollback guard: if a retuned attempt degrades by >10% relative to previous, revert to best known weights.
- Exit early when deviation `<= 5%`.

This satisfies rule-based adaptive reweighting, max-retry budget, and rollback behavior.
