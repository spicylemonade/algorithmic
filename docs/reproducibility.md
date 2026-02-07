# Reproducibility and Environment Requirements

## Hardware Assumptions
- CPU: 4+ cores recommended
- RAM: 8 GB minimum
- Disk: 2 GB free for outputs/artifacts

## Software
- Python 3.10+
- Standard library modules + `requests`
- Network access for external repositories/APIs

## Deterministic Seeding
- Global seed fixed at `42`
- Stochastic modules and scripts use deterministic `random.Random(42)` policy

## Reproduction Command Sequence
1. `python scripts/run_baseline_convex.py`
2. `python scripts/run_sparse_pole_tests.py`
3. `python scripts/run_uq_demo.py`
4. `python scripts/run_blind_validation.py`
5. `python scripts/run_sparse_ablation.py`
6. `python scripts/select_candidates.py --neo-limit 140`

## Output Locations
- JSON results: `results/`
- Figures: `figures/`
- Mesh artifacts: `results/blind_validation/models/`

## Notes
- Remote-source latency may affect runtime.
- Candidate pool size in `select_candidates.py` controls network workload.
