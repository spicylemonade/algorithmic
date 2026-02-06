# Research Hypotheses and Success Criteria

1. **H1 (Search efficiency)**: Progressive widening + legality-aware factorization increases model Elo by **>= 180** over shallow-search baseline at equal inference budget.
2. **H2 (Policy quality)**: AlphaGo-style self-play policy reaches **>= 62% win rate** versus heuristic baseline in 1,000-game arena.
3. **H3 (Training efficiency)**: Mixed precision + batched inference reduces training cost to **<= 0.75 GPU-hours per +10 Elo** (>=25% cost reduction from baseline 1.0).
4. **H4 (Inference latency)**: Median move decision latency at 800 simulations remains **<= 180 ms** on reference GPU tier.
5. **H5 (Generalization)**: On unseen opening distributions, Elo drop remains **<= 70 points** relative to in-distribution evaluation.

## Falsification Rules
- A hypothesis is rejected if the 95% confidence interval excludes the target threshold.
- Promotion to next research stage requires H1-H4 all passing and no catastrophic regression in legality violations.
