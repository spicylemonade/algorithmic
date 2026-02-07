# Uncertainty Quantification Framework

Approach:
- Run multi-start ensembles with deterministic seed base (`42`) and fixed perturbation policy.
- Compute 95% confidence intervals from empirical distributions for:
  - pole longitude (`lambda`)
  - pole latitude (`beta`)
  - period (`P`)
  - key shape dimensions (`axis_a`, `axis_b`, `axis_c`)

Computation:
- Percentile CI: [2.5%, 97.5%]
- Center reported as ensemble mean.

Implementation:
- `src/lci/uncertainty.py`
- Demonstration run: `scripts/run_uq_demo.py`
- Output: `results/item_014_uncertainty_framework.json`
