from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol

from .env import Action, FiveDChessEnv


class Agent(Protocol):
    def select_action(self, env: FiveDChessEnv, legal_actions: list[Action], rng: random.Random) -> Action:
        ...


@dataclass
class RandomAgent:
    def select_action(self, env: FiveDChessEnv, legal_actions: list[Action], rng: random.Random) -> Action:
        return legal_actions[rng.randrange(len(legal_actions))]


@dataclass
class HeuristicAgent:
    # Piece values aligned to white perspective; absolute values are used for capture utility.
    piece_values: dict[str, int] = None

    def __post_init__(self) -> None:
        if self.piece_values is None:
            self.piece_values = {
                "P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100,
                "p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 100,
            }

    def select_action(self, env: FiveDChessEnv, legal_actions: list[Action], rng: random.Random) -> Action:
        best_score = -10**9
        best = []
        for a in legal_actions:
            board = env.boards[(a.dst_timeline, a.dst_time)] if a.src_time != a.dst_time else env.boards[(a.src_timeline, a.src_time)]
            captured = board[a.dst_row][a.dst_col]
            score = self.piece_values.get(captured, 0)
            if a.src_time != a.dst_time:
                score += 1
            if score > best_score:
                best_score = score
                best = [a]
            elif score == best_score:
                best.append(a)
        return best[rng.randrange(len(best))]


@dataclass
class ShallowSearchAgent:
    """Depth-1 lookahead using a fast material proxy."""

    def _material(self, env: FiveDChessEnv) -> int:
        values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100}
        score = 0
        for b in env.boards.values():
            for row in b:
                for p in row:
                    if p == ".":
                        continue
                    v = values.get(p.upper(), 0)
                    score += v if p.isupper() else -v
        return score

    def select_action(self, env: FiveDChessEnv, legal_actions: list[Action], rng: random.Random) -> Action:
        # Limit branching for throughput during large benchmark batches.
        if len(legal_actions) > 12:
            legal_actions = sorted(
                legal_actions,
                key=lambda a: (
                    a.src_time != a.dst_time,
                    a.dst_row,
                    a.dst_col,
                ),
                reverse=True,
            )[:12]
        best_val = -10**9 if env.side_to_move == "W" else 10**9
        best = []
        for a in legal_actions:
            sim = _clone_env(env)
            sim.step(a)
            val = self._material(sim)
            better = val > best_val if env.side_to_move == "W" else val < best_val
            if better:
                best_val = val
                best = [a]
            elif val == best_val:
                best.append(a)
        return best[rng.randrange(len(best))]


def _clone_env(env: FiveDChessEnv) -> FiveDChessEnv:
    sim = FiveDChessEnv(max_moves=env.max_moves)
    sim.rng = random.Random(env.seed)
    sim.seed = env.seed
    sim.move_count = env.move_count
    sim.side_to_move = env.side_to_move
    sim.next_timeline_id = env.next_timeline_id
    sim.done = env.done
    sim.boards = {k: [row[:] for row in b] for k, b in env.boards.items()}
    sim.timeline_latest = dict(env.timeline_latest)
    return sim


@dataclass
class StrongAgent:
    """Stronger candidate with limited two-ply minimax over pruned actions."""

    def _material(self, env: FiveDChessEnv) -> int:
        values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100}
        score = 0
        for b in env.boards.values():
            for row in b:
                for p in row:
                    if p == ".":
                        continue
                    score += values.get(p.upper(), 0) if p.isupper() else -values.get(p.upper(), 0)
        return score

    def _score(self, env: FiveDChessEnv) -> float:
        m = self._material(env)
        return float(m)

    def select_action(self, env: FiveDChessEnv, legal_actions: list[Action], rng: random.Random) -> Action:
        if len(legal_actions) > 6:
            legal_actions = sorted(legal_actions, key=lambda a: (a.src_time != a.dst_time, a.dst_row, a.dst_col), reverse=True)[:6]
        maximize = env.side_to_move == "W"
        best_val = -10**9 if maximize else 10**9
        best_actions = []

        for a in legal_actions:
            s1 = _clone_env(env)
            s1.step(a)
            opp_actions = s1.legal_actions()
            if len(opp_actions) > 4:
                opp_actions = sorted(opp_actions, key=lambda x: (x.src_time != x.dst_time, x.dst_row, x.dst_col), reverse=True)[:4]
            if not opp_actions:
                val = self._score(s1)
            else:
                vals = []
                for oa in opp_actions:
                    s2 = _clone_env(s1)
                    s2.step(oa)
                    vals.append(self._score(s2))
                val = min(vals) if maximize else max(vals)
            better = val > best_val if maximize else val < best_val
            if better:
                best_val = val
                best_actions = [a]
            elif val == best_val:
                best_actions.append(a)

        return best_actions[rng.randrange(len(best_actions))]
