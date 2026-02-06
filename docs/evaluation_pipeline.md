# Evaluation Pipeline (Item 009)

Implemented unified tournament harness in `src/fived/eval.py` with:
- `run_head_to_head(...)` for balanced two-agent matches
- `run_round_robin(...)` for full pairwise tournaments
- Elo + 95% CI estimation from match scores

Validation result:
- Head-to-head CI width converged to <=80 Elo after scheduled budget (5,000 games).
- Full outputs stored in `results/item_009_evaluation_pipeline.json`.
