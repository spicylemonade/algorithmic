# Sparse Photometry Inversion Constraints (Durech-Style)

## Minimum Data Assumptions
Sparse-mode activation requires one of:
- `N_sparse >= 100` calibrated points spanning at least 3 apparitions, or
- `N_sparse >= 70` with phase-angle span `>= 25 deg` and solar elongation diversity.

Additional quality filters:
- photometric uncertainty per point `< 0.15 mag`
- outlier rejection by robust MAD threshold `3.5`

## Period Search Bounds and Resolution
- Global period bounds: `P in [2 h, 200 h]`.
- Coarse scan: step `1e-2 h`.
- Mid refinement around top 20 peaks: step `1e-3 h`.
- Fine refinement around top 5 peaks: step `1e-4 h`.

## Pole Search Strategy
- Coarse sphere grid: 10 deg spacing in ecliptic longitude/latitude.
- Refined local tessellation around top period-pole combinations:
  - stage 2 spacing 5 deg
  - stage 3 spacing 2 deg

## Pole Ambiguity Handling
- Evaluate mirror pole pair solutions `(lambda, beta)` and `(lambda+180 deg, -beta)`.
- Keep both until dense-data or multi-apparition residual discrimination exceeds threshold:
  - `Delta RMS >= 0.015 mag` OR
  - spin-axis prior consistency from external constraints.
- If unresolved, propagate both solutions to downstream queue with ambiguity flag.

## Sparse Objective Adaptation
In sparse mode, increase priors and smoothness weights:
- `w_data = 1.0`
- `w_smooth = 0.25`
- `w_spin = 0.15`
- `w_concavity = 0.05` (de-emphasize overfitting to sparse noise)

## Exit Criteria
Sparse solve accepted when:
- best-fit residual `< 0.12 mag`
- period uncertainty `< 0.2%`
- pole confidence cone radius `< 20 deg` at 95% from ensemble runs (seed anchored at 42)
