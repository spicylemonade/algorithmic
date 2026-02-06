# Canonical 5D Engine API

- `GameEngine5D.legal_moves(state: GameState) -> list[Move]`
- `GameEngine5D.legal_moves_reference(state: GameState) -> list[Move]`
- `GameEngine5D.apply(state: GameState, move: Move) -> GameState`
- `GameEngine5D.state_to_dict(state: GameState) -> dict`

Determinism contract:
- Move lists are sorted lexicographically.
- Engine behavior is pure for a fixed input state.
- Regression tests run with fixed seed `42`.
