# Baseline Pipeline Architecture

## Stage Diagram
`[1 ingestion] -> [2 preprocessing] -> [3 geometry] -> [4 convex solver] -> [5 non-convex solver] -> [6 sparse solver] -> [7 validation] -> [8 ranking] -> [9 export]`

## Module Contracts
1. `ingestion`
- Input: repository/source descriptors (ALCDEF/PDS/Gaia/ZTF/MPC/DAMIT/JPL)
- Output: normalized observation tables and metadata records

2. `preprocessing`
- Input: raw observation rows
- Output: cleaned photometry (bias-corrected, outlier flags, uncertainty columns)

3. `geometry`
- Input: cleaned rows + ephemerides
- Output: sun/object/observer unit vectors, phase angles, apparition IDs

4. `convex_solver`
- Input: geometry-enriched photometry + initialization priors
- Output: convex mesh parameters, spin state, residual profile

5. `non_convex_solver`
- Input: convex solution state + residual structure
- Output: refined non-convex mesh parameters, updated spin state

6. `sparse_solver`
- Input: sparse-only or sparse-dominant photometry subset
- Output: pole/period posterior candidates and ambiguity scores

7. `validation`
- Input: predicted mesh + held-out photometry + ground-truth mesh
- Output: Hausdorff, volumetric IoU, RMSE, pole-angle error, confidence score

8. `ranking`
- Input: candidate-level metrics + boolean eligibility filters
- Output: ranked target table with evidence fields and confidence

9. `export`
- Input: selected candidate solution objects
- Output: `.obj` mesh, spin vector files, JSON manifests, report tables
