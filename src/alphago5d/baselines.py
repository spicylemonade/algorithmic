from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .engine import GameEngine5D
from .types import GameState, Move, Piece

PIECE_VALUE = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 50}


@dataclass
class SearchStats:
    nodes: int = 0
    elapsed: float = 0.0


class Agent:
    name = "agent"

    def choose(self, state: GameState, engine: GameEngine5D, rng: random.Random, stats: SearchStats) -> Move:
        raise NotImplementedError


class RandomAgent(Agent):
    name = "random"

    def choose(self, state: GameState, engine: GameEngine5D, rng: random.Random, stats: SearchStats) -> Move:
        t0 = time.perf_counter()
        moves = engine.legal_moves(state)
        stats.nodes += len(moves)
        stats.elapsed += time.perf_counter() - t0
        return rng.choice(moves)


class AlphaBetaAgent(Agent):
    name = "alphabeta"

    def __init__(self, depth: int = 2):
        self.depth = depth

    def choose(self, state: GameState, engine: GameEngine5D, rng: random.Random, stats: SearchStats) -> Move:
        t0 = time.perf_counter()
        moves = engine.legal_moves(state)
        best_score = -10**9
        best = moves[0]
        for m in moves:
            nxt = engine.apply(state, m)
            score = -self._search(nxt, engine, self.depth - 1, -10**9, 10**9, stats)
            if score > best_score:
                best_score = score
                best = m
        stats.elapsed += time.perf_counter() - t0
        return best

    def _search(self, s: GameState, engine: GameEngine5D, depth: int, alpha: float, beta: float, stats: SearchStats) -> float:
        moves = engine.legal_moves(s)
        stats.nodes += len(moves)
        if depth == 0 or not moves:
            return evaluate(s)
        best = -10**9
        for m in moves:
            v = -self._search(engine.apply(s, m), engine, depth - 1, -beta, -alpha, stats)
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best


class MCTSAgent(Agent):
    name = "mcts"

    def __init__(self, simulations: int = 40, c: float = 1.4):
        self.simulations = simulations
        self.c = c

    def choose(self, state: GameState, engine: GameEngine5D, rng: random.Random, stats: SearchStats) -> Move:
        t0 = time.perf_counter()
        root_moves = engine.legal_moves(state)
        if len(root_moves) == 1:
            stats.nodes += 1
            stats.elapsed += time.perf_counter() - t0
            return root_moves[0]
        wins = [0.0] * len(root_moves)
        visits = [0] * len(root_moves)

        for _ in range(self.simulations):
            total = sum(visits) + 1
            best_i = 0
            best_u = -10**9
            for i in range(len(root_moves)):
                if visits[i] == 0:
                    u = 10**6
                else:
                    q = wins[i] / visits[i]
                    u = q + self.c * math.sqrt(math.log(total) / visits[i])
                if u > best_u:
                    best_u = u
                    best_i = i

            st = engine.apply(state, root_moves[best_i])
            val = self._rollout(st, engine, rng, stats)
            visits[best_i] += 1
            wins[best_i] += val

        best = max(range(len(root_moves)), key=lambda i: visits[i])
        stats.elapsed += time.perf_counter() - t0
        return root_moves[best]

    def _rollout(self, state: GameState, engine: GameEngine5D, rng: random.Random, stats: SearchStats) -> float:
        st = state
        for _ in range(2):
            moves = engine.legal_moves(st)
            stats.nodes += len(moves)
            if not moves:
                return -1.0
            st = engine.apply(st, rng.choice(moves))
        score = evaluate(st)
        return 1.0 if score > 0 else (0.5 if score == 0 else 0.0)


def evaluate(state: GameState) -> float:
    total = 0.0
    for board in state.boards.values():
        for p in board.values():
            val = PIECE_VALUE[p.kind]
            total += val if p.color == state.active_player else -val
    return total


def random_initial_state(rng: random.Random) -> GameState:
    boards = {}
    for l in [0]:
        for t in [0]:
            board: Dict[Tuple[int, int], Piece] = {}
            for _ in range(rng.randint(4, 8)):
                sq = (rng.randint(0, 7), rng.randint(0, 7))
                if sq in board:
                    continue
                board[sq] = Piece(color=rng.choice(["W", "B"]), kind=rng.choice(list(PIECE_VALUE.keys())))
            boards[(l, t)] = board
    return GameState(boards=boards, active_player=rng.choice(["W", "B"]), max_timeline=1)


def play_game(
    engine: GameEngine5D,
    white: Agent,
    black: Agent,
    rng: random.Random,
    max_plies: int = 10,
) -> Tuple[float, Dict[str, SearchStats]]:
    st = random_initial_state(rng)
    stats = {white.name: SearchStats(), black.name: SearchStats()}
    for _ in range(max_plies):
        moves = engine.legal_moves(st)
        if not moves:
            winner = -1.0 if st.active_player == "W" else 1.0
            return winner, stats
        if st.active_player == "W":
            mv = white.choose(st, engine, rng, stats[white.name])
        else:
            mv = black.choose(st, engine, rng, stats[black.name])
        st = engine.apply(st, mv)
    score = evaluate(st)
    if score > 0:
        return 1.0, stats
    if score < 0:
        return -1.0, stats
    return 0.0, stats
