# LCI Research Objective and Success Criteria

## Objective
Develop a custom Light Curve Inversion (LCI) engine that improves shape and spin recovery accuracy for asteroids, with a specific advantage on sparse photometric inputs. The engine must synthesize convex optimization, non-convex evolutionary search, and sparse-data handling into a reproducible pipeline that can be validated against ground-truth meshes and then applied to previously un-modeled NEAs and large MBAs.

Primary claim to test: the custom engine should outperform current baseline workflows (MPO LCInvert-like convex-only, SAGE-like non-convex-only, KOALA-like multi-data optimization baseline approximations in this repo) in combined period/pole/mesh accuracy and sparse-data robustness.

## Evaluation Scope
- Validation set: objects with high-confidence DAMIT/JPL radar meshes.
- Deployment set: NEAs and MBAs with diameter >100 km and not present in DAMIT.
- Data regimes: dense, sparse, and mixed photometry.

## Quantitative KPIs (Baseline vs Target)
| KPI | Baseline (reference workflows) | Target (custom LCI) |
|---|---:|---:|
| 1. Sparse pole recovery rate (<=100 points, <=20 restarts) | 0.62 | >=0.78 |
| 2. Rotation period relative error median | 1.2% | <=0.5% |
| 3. Pole angular error median | 18 deg | <=10 deg |
| 4. Mesh Hausdorff deviation (normalized) | 8.5% | <=5.0% |
| 5. Volumetric IoU median | 0.83 | >=0.92 |
| 6. Dense-data fit residual (MAE mag) | 0.032 | <=0.020 |
| 7. Sparse ambiguity rate (multi-pole degeneracy) | 0.35 | <=0.20 |

## Go/No-Go Criteria
- Must satisfy KPI #1, #3, #4, and #5 simultaneously on benchmark aggregate.
- Any object with normalized mesh deviation >5% triggers recursive retuning and rerun.
- Final claim of superiority requires statistically significant aggregate gain over internal baseline implementations.

## Success Definition for Target Selection Stage
- Produce top-50 candidate list passing all four priority rules.
- Export model artifacts with spin vectors and uncertainty estimates.
- Provenance and reproducibility metadata must be complete for each result.
