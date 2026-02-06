# Final Technical Specification (Item 023)

## Architecture
- Environment: `src/fived/env.py` deterministic timeline-branching mini-5D chess API.
- Encoders: `src/fived/learning.py` tensor-stack and graph-style representations.
- Policy/Value: `src/fived/policy_value.py` with legal-action masking and bounded value output.
- Search: `src/fived/mcts.py` PUCT variant with optional transpositions.
- Training: `src/fived/self_play.py` staged curriculum + league windows + reanalysis.

## Data Pipeline
1. Generate self-play traces by stage (`run_item_014`).
2. Encode states/actions with `src/fived/schema.py`.
3. Train value head on material-tanh targets (`build_dataset` + linear fit).
4. Evaluate with tournament harness (`src/fived/eval.py` / `run_item_019`).

## Hyperparameters
- Seed: `42`
- Board size: `4x4`
- Max timelines encoded: `8`
- Max time depth encoded: `16`
- MCTS simulations: `48` (baseline experiments)
- Self-play stage max moves: `8, 10, 12, 14`
- Reanalysis factor: `25`

## Compute Profile
- CPU-only workflow validated in this run.
- Optional GPU not required for current lightweight models.

## Exact Repro Commands
```bash
PYTHONPATH=src python -m fived.benchmark
PYTHONPATH=src python -m fived.eval
PYTHONPATH=src python -m fived.learning
PYTHONPATH=src python -m fived.policy_value
PYTHONPATH=src python -m fived.mcts
PYTHONPATH=src python -m fived.self_play
PYTHONPATH=src python -m fived.novelty
PYTHONPATH=src python - <<'PY'
from fived.experiments import run_item_016, run_item_017, run_item_018, run_item_019, run_item_020
run_item_016(); run_item_017(); run_item_018(); run_item_019(); run_item_020()
PY
```
