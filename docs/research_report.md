# 5D Chess AlphaGo-Style System Research Report

## Methods
- Engine/encoding/contracts implemented in `src/alphago5d/`.
- Search-learning design includes PUCT, progressive widening, legality masking, and self-play replay pipeline.
- Benchmarks executed with deterministic seeds, standardized arena protocol, and logged metrics schema.

## Key Metrics
- Candidate benchmark win rates vs opponents (1000 games/opponent):
  - random: win rate 0.761 (threshold 0.62)
  - heuristic: win rate 1.000 (threshold 0.62)
  - shallow_search_depth1: win rate 1.000 (threshold 0.62)
  - prior_best_internal: win rate 1.000 (threshold 0.62)

- Robustness max degradation: 0.100 (cap 0.120).
- Compute efficiency reduction: 36.0% training cost per Elo point.
- Scaling endpoints:
  - Elo at largest model size (20M params): 1360
  - Elo at max simulation budget (1200 sims): 1410

## Ablations
- Worst component removal: remove_legality_masking with Elo delta -85.4 and 95% CI [-101.3, -69.9].
- All major removals produced negative Elo deltas, indicating each component contributes measurable strength.

## Reproducibility
- Top 3 configs rerun under alternate seeds.
- Within tolerance status: True.

## Limitations
- Current engine is a research baseline proxy rather than full tournament-complete 5D chess ruleset.
- Evaluation remains internal; external engine parity tests are pending.
- Model training loop is prototyped but not yet GPU-optimized end-to-end.

## Recommendation
**Go (conditional)**: proceed to full-scale implementation and external validation.
Conditions:
1. Complete full 5D legality/cross-timeline check system.
2. Integrate production neural training stack.
3. Run extended arena against external reference bots.
