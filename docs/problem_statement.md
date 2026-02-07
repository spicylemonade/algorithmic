# End-to-End Research Objective and Success Thresholds

## Objective
Develop and execute a custom Light Curve Inversion (LCI) software pipeline that reconstructs 3D asteroid shapes and spin states from dense and sparse photometry, with emphasis on robust performance under sparse survey data. The system must produce:

1. A ranked list of 50 high-priority modeling candidates (previously un-modeled NEAs or large MBAs).
2. For each selected candidate, a reconstructed shape mesh (`.obj`) and spin-vector output.
3. A validation report against known reference models from DAMIT and JPL radar-derived shapes.

## Scope
The solver architecture will combine three methodological pillars:

- Convex gradient-based inversion (Kaasalainen-Torppa-style) for stable global shape initialization.
- Evolutionary non-convex refinement (SAGE-inspired) to recover major concavity structures.
- Sparse-mode inversion (Durech-style constraints and search strategy) for limited cadence survey data.

## Quantitative Success Criteria
Primary quantitative gate:

- Validation deviation against ground-truth meshes must be below 5% aggregate error threshold.

Deviation is measured using:

- Symmetric Hausdorff distance normalized by characteristic diameter.
- Volumetric IoU complement (`1 - IoU`) where applicable.
- Spin-axis angular error and period error as secondary checks.

Pass condition for promotion from validation to production-target modeling:

- Mean composite deviation < 5% and no benchmark target > 10% deviation.

## Deliverables
Required final outputs:

- Source code implementing ingestion, geometry, photometry forward model, convex solver, evolutionary solver, sparse solver, and validation modules.
- Benchmark validation artifacts: per-target predictions, logs, convergence traces, and metric tables.
- Top-50 candidate list with filtering evidence for all priority rules.
- Produced `obj` meshes and spin vectors for selected targets.

## Reproducibility Policy
- Deterministic seed policy: seed = 42 for stochastic components.
- All experiment outputs stored as JSON in `results/`.
- All plots stored as PNG in `figures/`.
- Every rubric item tracked with pre/post status update in `research_rubric.json`.
