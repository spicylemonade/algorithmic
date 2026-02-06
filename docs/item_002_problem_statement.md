# Custom LCI Research Objective

## Problem Statement
Current asteroid light-curve inversion systems often lose reliability on sparse survey photometry and under-model non-convex shape structure. This project builds a custom from-scratch inversion engine that fuses convex gradient optimization, evolutionary non-convex refinement, and sparse-aware pole/period search. The immediate mission is to generate high-confidence 3D shape and spin models for previously unmodeled Near-Earth Asteroids (NEAs) and large Main Belt Asteroids (MBAs), while validating accuracy against independent ground-truth meshes.

## Scope and Constraints
- Core inversion logic is implemented in local project code (`src/lci`) rather than delegating optimization internals to specialized inversion libraries.
- Validation uses blind reconstruction from raw photometry prior to geometric comparison against DAMIT/JPL reference meshes.
- Selection logic must prioritize NEO status or diameter > 100 km, robust rotational period quality, absent DAMIT model, and sufficient photometric coverage.

## Quantitative Success Targets
1. Shape reconstruction deviation target: normalized geometric deviation < 5% on validation objects, measured using normalized Hausdorff and (1 - volumetric IoU).
2. Sparse-data pole recovery target: >= 80% correct pole-hemisphere recovery for validation experiments that use sparse-only or sparse-dominant data.
3. Candidate ranking target: precision@50 >= 0.70 where a true positive is a candidate later confirmed to pass confidence threshold and physical consistency checks.
4. Stability target: deterministic reruns with fixed seed (`42`) differ by <= 1% on key metrics for pilot objects.

## Primary Deliverables
- Source engine: convex solver, evolutionary solver, sparse solver, metrics, validation loop, ranking.
- Validation report with per-object metrics, convergence, and threshold pass/fail.
- Top-50 candidate list with evidence fields and generated `.obj`/spin-vector outputs for high-confidence subset.
