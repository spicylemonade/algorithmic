# Light Curve Inversion Final Report

## 1. Executive Summary
- Objective
- Key outcomes
- Pass/fail status

## 2. Methods
- Convex inversion module
- Non-convex evolutionary module
- Sparse inversion module
- Data fusion/calibration

## 3. Validation Against Ground Truth
- Cohort definition
- Blinded protocol
- Metrics: normalized Hausdorff, IoU, photometric RMS, pole-direction error
- Threshold checks

## 4. Candidate Discovery
- Boolean filter logic
- Ranking formula and tie-breaks
- Top-50 table with confidence and coverage

## 5. Deliverables
- Mesh files (.obj)
- Spin vectors and period estimates
- Uncertainty intervals
- Provenance manifests

## 6. Comparative Benchmark
- Shared dataset matrix
- Tool-by-tool metric summary

## 7. Reproducibility Checklist
- Fixed random seed = 42
- Input dataset manifest hash
- Config hash
- Code commit hash
- Exact rerun commands

## 8. Rerun Instructions
```bash
python main.py --seed 42 --config configs/default.json --targets results/top50_candidates.json
```
