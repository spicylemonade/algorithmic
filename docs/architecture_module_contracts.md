# Baseline Architecture and Module Contracts

## Modules
- `GameEngine`: Maintains canonical 5D chess state, legal move generation, transition logic, and terminal adjudication.
- `StateEncoder`: Maps structured states to fixed-rank tensors and legality masks; supports deterministic decode for tests.
- `PolicyValueModel`: Produces policy logits and scalar value from encoded states; supports supervised/self-play updates.
- `MCTSPlanner`: Performs policy/value-guided tree search under simulation budget and returns root policy/value targets.
- `SelfPlayWorker`: Uses `GameEngine + MCTSPlanner` to generate trajectories for replay.
- `Evaluator`: Runs arena matches and aggregates Elo/win-rate/latency metrics.

## I/O Schemas
- Engine state: Python dict/dataclass containing timelines, board tensors, clocks, rights, and side-to-move.
- Move schema: `(src_timeline, src_time, src_square, dst_timeline, dst_time, dst_square, promotion, flags)`.
- Encoded state: tensor shape `(T, L, C, 8, 8)` plus legal-action mask over factorized action head.
- Model output: `policy_logits: float[A]`, `value: float in [-1,1]`.
- MCTS output: `(pi_root: float[A], v_root: float)`.

## Failure Modes
- Invalid state serialization: raise `ValueError` in engine/encoder.
- Illegal transition attempt: raise `RuntimeError` in engine `apply_move`.
- Tensor mismatch or NaN inference: raise `RuntimeError` in model.
- Search budget timeout: raise `TimeoutError` in planner.
- Self-play deadlock/no-legal-move nonterminal inconsistency: raise `AssertionError` in worker.
- Evaluator mismatch (different action space schemas): raise `ValueError`.
