# Quantitative Success Criteria and Phase Gates (Item 005)

## Core Metrics and Thresholds
- Hausdorff distance (normalized by target diameter): `<= 0.05` for validation set pass.
- Volumetric IoU (voxelized normalized meshes): `>= 0.95`.
- Lightcurve RMS residual (mag): dense `<= 0.03`, sparse `<= 0.06`.
- Spin-vector angular error (deg): `<= 8` against ground truth.
- Sparse pole-recovery rate: `>= 85%` within 10 deg across stress tests.
- Runtime budget: <= 4 hours per target on 16 CPU threads, <= 24 GB RAM.

## Phase Stop/Go Gates
- Phase 1 -> Phase 2: all design artifacts complete, schema validated.
- Phase 2 -> Phase 3: baseline engine and metrics scripts run reproducibly with seed 42.
- Phase 3 -> Phase 4: hybrid and sparse modules integrated and unit tested.
- Phase 4 -> Phase 5: all anchor asteroids meet Hausdorff<=5% and IoU>=95%, or iteration cap reached with documented failures.

## Recursive Optimization Rule
- If any target has deviation >5%:
  - adjust loss weights (`w_photo`, `w_smooth`, `w_concavity`),
  - tighten period-grid granularity,
  - rerun blinded inversion.
- Maximum iterations: 8 per anchor target.
- On cap exceedance: status `failed` and preserve diagnostics.

## Surpass-SOTA Criteria
- Must outperform baseline references on sparse regime:
  - `RMS_sparse` at least 10% lower than configured baselines.
  - Pole error median at least 15% lower than baseline median.
