# Reproducibility Runbook

## Environment
1. Python `3.11+`
2. Install dependencies:
   - `pip install -r requirements.txt`

## Fixed Seeds
- Primary seed: `42`
- Additional deterministic lists: `results/item_023_seed_list.json`

## Reproducing Headline Metrics
1. Baseline benchmark:
   - `PYTHONPATH=src python3 scripts/run_item_008_benchmarks.py`
2. Rated benchmark:
   - `python3 scripts/run_item_017_benchmark.py`
3. Efficiency frontier:
   - `PYTHONPATH=src:scripts python3 scripts/run_item_018_efficiency.py`

## Config Snapshots
- Stored in `results/item_023_config_snapshots.json`
- Include search settings, game counts, and evaluation protocol lock.

## Verification Rule
- Recompute headline Elo metrics over 3 reruns; target <=5% relative deviation.
