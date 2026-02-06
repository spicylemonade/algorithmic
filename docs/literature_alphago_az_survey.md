# AlphaGo/AlphaZero-Style Search-Learning Survey

## Primary References
1. Silver et al. (2016), *Mastering the game of Go with deep neural networks and tree search*.
2. Silver et al. (2017), *Mastering the game of Go without human knowledge*.
3. Silver et al. (2018), *A general reinforcement learning algorithm that masters chess, shogi, and Go*.
4. Schrittwieser et al. (2020), *Mastering Atari, Go, chess and shogi by planning with a learned model* (MuZero).
5. Tian et al. (2019), *ELF OpenGo*.
6. Anthony et al. (2017), *Thinking Fast and Slow with Deep Learning and Tree Search*.
7. Hubert et al. (2021), *Learning and Planning in Complex Action Spaces*.
8. Grill et al. (2020), *Monte-Carlo Tree Search as Regularized Policy Optimization*.
9. Cazenave (2022), *Monte Carlo Search for Very Large Action Spaces*.
10. Ye et al. (2021), *Mastering Chinese Chess and Beyond from Self-Play*.
11. Wang et al. (2021), *EfficientZero*.
12. Schrittwieser et al. (2021), *Online and Offline Reinforcement Learning by Planning with a Learned Model*.

## Extracted Design Choices
- **Policy target**: Use MCTS visit-count distribution `pi_MCTS` with temperature annealing; enforce legality mask before normalization.
- **Value target**: Use terminal game result `z in {-1,0,1}`; optionally blend n-step bootstrapped value for long-horizon stabilization.
- **Loss**: `L = CE(pi_MCTS, pi_theta) + MSE(v_theta, z) + c||theta||^2`; add entropy regularization early in curriculum.
- **Search selection**: PUCT with prior and dynamic exploration coefficient; optional Gumbel/implicit minimax backups for wide branching.
- **Expansion control**: Progressive widening and policy-threshold pruning to keep effective branching tractable.
- **Backpropagation**: Perspective-correct value sign flips and optional variance-aware value normalization.
- **Self-play regime**: Distributed asynchronous workers with model snapshot gating and replay freshness constraints.
- **Replay sampling**: Prioritize recent games with tempered uniform mixing to avoid policy collapse and stale targets.
- **Resignation logic**: Conservative, calibrated threshold with random no-resign probes for bias correction.
- **Promotion criteria**: Arena match with SPRT/Elo confidence gates before replacing best model.

## Implications for 5D Chess
- Extreme action spaces require **factorized policy heads + progressive widening**.
- Temporal branching benefits from **transposition tables keyed by timeline hashes**.
- Throughput bottlenecks shift from network inference to legality masking and move generation; vectorized masks become first-class.
