# Baseline Convex Inversion Experiment Protocol

## Deterministic Setup
- Seeds: `[42, 42, 42]` (three deterministic restarts with distinct deterministic initial states).
- Initialization strategy:
  - Run A: ellipsoid `(1.0, 0.9, 0.8)`, pole `(120, 30)`, `P=6.0 h`
  - Run B: ellipsoid `(1.0, 0.85, 0.75)`, pole `(150, 20)`, `P=5.8 h`
  - Run C: ellipsoid `(1.0, 0.95, 0.9)`, pole `(90, 40)`, `P=6.2 h`

## Hyperparameters
- Convex solver step size: `0.05`
- Max iterations: `300`
- Stop when step size `< 1e-4` or objective no longer improves

## Required Outputs
For each run:
- Photometric residual RMS
- Recovered pole `(lambda, beta)`
- Recovered period `P`

## Execution Command
`python scripts/run_baseline_convex.py`
