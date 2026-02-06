# Reproducible Runbook

## Setup
1. Python 3.10+
2. Run from repository root

## Data acquisition
- Ground-truth set: `results/item_016_ground_truth_set.json`
- Validation runs: `results/item_017_blind_runs.json`

## Execution
- Pilot run: `python main.py --seed 42 --out results/main_run.json`
- Determinism check: `python tools/check_rerun_tolerance.py`

## Expected outputs
- JSON artifacts in `results/`
- PNG figures in `figures/`
- Mesh outputs in `models/`

## Reproduction tolerance
- Key pilot metrics (`period_evo`, `loss_evo`) must reproduce within `<=1%` relative variance.
