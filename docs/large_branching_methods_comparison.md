# Methods for Large-Branching Board Games

| Method | Branching-Factor Strategy | Sample Efficiency | Compute Cost | Known Limitations |
|---|---|---|---|---|
| AlphaZero PUCT | Prior-guided expansion with fixed topological action space | Medium | High (many simulations) | Struggles when legal action count is extremely sparse but huge-indexed |
| Progressive Widening MCTS | Expand only top-k actions as visit count grows | Medium-High | Medium-High | Sensitive to widening schedule hyperparameters |
| Gumbel MuZero | Sequential halving / Gumbel sampling over candidate actions | High | High (model-based rollout overhead) | Requires accurate dynamics model; training instability risk |
| Policy-Gradient + Beam Search | Learn policy, apply beam-pruned lookahead | Medium | Medium | Beam misses tactical outliers; limited value backup quality |
| Implicit Minimax MCTS | Blend rollout/value backups with minimax-style terms | Medium | Medium-High | Backup tuning brittle across domains |
| Action-Factorized Policy + MCTS | Factor move into components with legality masks | High in sparse legal sets | Medium | Error propagation if early factors are mispredicted |
| Hierarchical Candidate Generation | Two-stage (candidate proposal then detailed search) | High | Low-Medium | Candidate generator bias can cap ceiling performance |
