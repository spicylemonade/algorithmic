from __future__ import annotations

import random

from .contracts import Move
from .engine import BaselineRuleEngine, BaselineState


class RandomAgent:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def select_move(self, engine: BaselineRuleEngine, state: BaselineState) -> Move:
        return self.rng.choice(engine.legal_moves(state))


class HeuristicAgent:
    def select_move(self, engine: BaselineRuleEngine, state: BaselineState) -> Move:
        best_move = None
        best_score = -10**9
        for move in engine.legal_moves(state):
            next_state = engine.apply_move(state, move)
            score = engine.material_score(next_state, state.side_to_move)
            if score > best_score:
                best_score = score
                best_move = move
        assert best_move is not None
        return best_move


class ShallowSearchAgent:
    def __init__(self, depth: int = 2):
        self.depth = depth

    def _minimax(self, engine: BaselineRuleEngine, state: BaselineState, depth: int, root_color: int) -> int:
        if depth == 0 or engine.is_terminal(state):
            return engine.material_score(state, root_color)
        moves = engine.legal_moves(state)
        if not moves:
            return engine.material_score(state, root_color)
        if state.side_to_move == root_color:
            return max(self._minimax(engine, engine.apply_move(state, m), depth - 1, root_color) for m in moves)
        return min(self._minimax(engine, engine.apply_move(state, m), depth - 1, root_color) for m in moves)

    def select_move(self, engine: BaselineRuleEngine, state: BaselineState) -> Move:
        root_color = state.side_to_move
        best_move = None
        best_score = -10**9
        for move in engine.legal_moves(state):
            score = self._minimax(engine, engine.apply_move(state, move), self.depth - 1, root_color)
            if score > best_score:
                best_score = score
                best_move = move
        assert best_move is not None
        return best_move
