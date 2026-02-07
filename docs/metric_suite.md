# Mesh and Spin Metric Suite

## Metrics
1. Normalized symmetric Hausdorff distance:
   - `d_H(P,T) = max{sup_p inf_t ||p-t||, sup_t inf_p ||t-p||}`
   - `d_H_norm = d_H / D_T`, where `D_T` is characteristic truth diameter.

2. Volumetric IoU:
   - `IoU = Vol(P ∩ T) / Vol(P ∪ T)`
   - Deviation term used in gate: `1 - IoU`.

3. Spin-axis angular error:
   - `e_spin = arccos(s_pred · s_true)` (degrees)
   - Current baseline proxy reports latitude-difference bound; full angular form retained for final runs.

4. Period error:
   - `e_P = |P_pred - P_true|` (hours)

## Pass/Fail Thresholds
- `d_H_norm <= 0.05`
- `1 - IoU <= 0.05`
- `e_spin <= 10 deg`
- `e_P <= 0.01 h`

A target is marked validated only if all thresholds pass.
