#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=.

./scripts/run_blinded_validation.py
./scripts/recursive_optimization.py
./scripts/run_ablations.py
./scripts/filter_candidates.py
./scripts/rank_top50.py
./scripts/package_outputs.py
