# Validation Report Template

## 1. Benchmark Setup
- Dataset manifest and partition policy
- Blind protocol statement
- Solver version, config hash, seed (42)

## 2. Per-Target Metrics Table
Columns:
- asteroid id/name
- Hausdorff normalized
- volumetric IoU
- spin-axis error
- period error
- composite deviation (%)
- pass/fail (`<5%` target)

## 3. Convergence Plots
- objective vs iteration (convex stage)
- fitness vs generation (evolutionary stage)
- sparse-search heatmap or scan trace

## 4. Error Analysis
- worst-target deep dives
- ambiguity cases (mirror poles)
- sensitivity to sparse coverage

## 5. Criteria Gate
- explicit statement: `validation deviation < 5%` passed/failed
- table of failed targets with likely causes and remediation action
