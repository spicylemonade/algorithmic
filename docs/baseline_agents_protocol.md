# Baseline Agents and Benchmark Protocol

## Agents
- `random`: uniformly samples from legal moves.
- `heuristic`: one-ply material-gain greedy policy.
- `shallow_search`: depth-2 minimax over deterministic baseline engine.

## Evaluation Protocol
- Round-robin matchups: random vs heuristic, random vs shallow, heuristic vs shallow.
- `500` games per matchup.
- Alternating colors each game.
- Fixed seed: `42`.
- Metrics: wins/losses/draws and win rate from agent A perspective.
