# MCTS Enhancements for Extreme Branching

## Core Equations
- Selection (PUCT):
  `a* = argmax_a [ Q(s,a) + c_puct * P(s,a) * sqrt(N(s)) / (1 + N(s,a)) ]`
- Progressive widening trigger:
  `|A_expanded(s)| <= k * N(s)^alpha`, with `k=2.0`, `alpha=0.45`.
- Backpropagation:
  `Q(s,a) <- (N(s,a)*Q(s,a) + v_child) / (N(s,a)+1)`, with player-perspective sign inversion on alternate plies.

## Enhancements
1. **Progressive widening**
   - Expected impact: 35-50% fewer low-value child expansions at fixed simulation budget.
2. **Virtual loss (parallel MCTS)**
   - Expected impact: 1.4-1.8x scaling efficiency with 8 search workers, reduced duplicate traversals.
3. **Legality-aware action pruning**
   - Expected impact: near-zero illegal expansions; 20-30% node budget reallocated to legal frontier.
4. **Transposition table across timelines**
   - Expected impact: 10-25% effective depth gain in repeated temporal motifs.
