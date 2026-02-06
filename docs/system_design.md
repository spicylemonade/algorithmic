# 5D AlphaGo-Style System Design

## Component Diagram

```mermaid
flowchart LR
  E[5D Engine\n(GameEngine5D)] --> X[Encoder\n(TensorCodec)]
  X --> N[Policy-Value Net]
  N --> M[PUCT MCTS]
  M --> S[Self-Play Generator]
  S --> R[Replay Buffer]
  R --> T[Trainer]
  T --> N
  M --> B[Baseline Arena]
  B --> Q[Evaluation Protocol]
  Q --> K[Tracking + Reports]
```

## Interface Contracts
- Engine: `src/alphago5d/engine.py`
  - `legal_moves`, `legal_moves_reference`, `apply`, `state_to_dict`.
- Encoding: `src/alphago5d/encoding.py`
  - `encode_state/decode_state`, `encode_action/decode_action`.
- Search: `src/alphago5d/mcts.py`
  - `PUCT.normalize_priors`, `expand`, `select`, `backup`.
- Baselines: `src/alphago5d/baselines.py`
  - `RandomAgent`, `AlphaBetaAgent`, `MCTSAgent`, `play_game`.
- Tracking: `src/alphago5d/tracking.py`
  - run metadata schema and persistence.
- Safety: `src/alphago5d/safety.py`
  - detector thresholds and triggers.

## Major Algorithmic Choices and Rationale
- Deterministic legal-move API with reference generator for correctness auditing.
- Sparse tensor encoding for portability and deterministic round-trips.
- PUCT for planning under large action sets with normalized priors.
- Curriculum-driven self-play and replay governance for stability.
- Efficiency add-ons: symmetry-aware caching and learned pruning gate.

## Experiment Cross-References
- Engine correctness: `results/item_006_legal_move_regression.json`
- Encoding validation: `results/item_007_encoding_roundtrip.json`
- Baselines: `results/item_008_baseline_benchmarks.json`
- Evaluation protocol: `results/item_009_power_analysis.json`
- Tracking reproducibility: `results/item_010_repro_check.json`
- Architecture ablation: `results/item_011_arch_ablation.json`
- PUCT invariants: `results/item_012_mcts_invariants.json`
- Curriculum targets: `results/item_013_curriculum_metrics.json`
- Efficiency methods: `results/item_014_efficiency_methods.json`
- Safety simulations: `results/item_015_safety_simulation.json`
- Controlled ablations: `results/item_016_ablation_runs.json`
- Rated benchmarking: `results/item_017_rated_benchmark.json`
- Compute/sample frontier: `results/item_018_efficiency_tradeoffs.json`
- Generalization suites: `results/item_019_generalization.json`
- Error taxonomy: `results/item_020_error_analysis.json`
- Hypothesis synthesis: `results/item_021_hypothesis_synthesis.json`

Coverage statement:
- All major design decisions are linked to at least one experimental artifact above.
