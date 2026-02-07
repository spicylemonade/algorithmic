# Solver Handoff Policy: Gradient -> Evolutionary

## Numeric Triggers
Handoff from convex gradient optimization to evolutionary non-convex refinement occurs when:
1. Convergence slope `> -1e-5` over recent window AND residual stagnation for `>=25` iterations AND mesh complexity proxy `>=0.3`.
2. Or flat slope `> -5e-6` with stagnation `>=40` iterations.

## Rollback Logic
After handoff, if evolutionary candidate loss worsens by more than 2% versus convex baseline, rollback to last convex checkpoint and reduce concavity weight.

## Why
- Prevent premature handoff before convex stabilization.
- Trigger non-convex exploration only when gradient path plateaus.
- Guard against instability/regression via deterministic rollback.

Implementation: `src/lci/handoff_policy.py`.
