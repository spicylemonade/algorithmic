# Validation Report Template (Item 023)

## 1. Executive Summary
- Dataset version and run metadata.
- Overall pass/fail against target thresholds.

## 2. Per-target Validation Table
Columns:
- target
- hausdorff_norm
- volumetric_iou
- lightcurve_rms
- spin_error_deg
- confidence
- pass_flag

## 3. Aggregate Statistics
- Mean/median/std for each metric.
- Pass rate across validation anchors.
- Sparse-regime subset statistics.

## 4. Baseline Comparisons
Explicit side-by-side metrics vs:
- MPO LCInvert
- SAGE
- KOALA

Include absolute and relative improvements:
- `delta_abs = ours - baseline`
- `delta_pct = (ours - baseline)/baseline`

## 5. Failure Analysis
- Targets failing any threshold.
- Suspected cause category (coverage/noise/degeneracy/model mismatch).
- Corrective action taken (loss reweighting, period refinement, etc.).

## 6. Reproducibility Appendix
- commit hash
- config hash
- data snapshot hash
- random seed (=42)
- command used
