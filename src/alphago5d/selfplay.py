from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .agents import ShallowSearchAgent
from .engine import BaselineRuleEngine


@dataclass
class ReplayEntry:
    state_hash: int
    policy_target: list[float]
    value_target: float
    game_index: int


class ReplayBuffer:
    def __init__(self, capacity: int = 50000):
        self.capacity = capacity
        self.items: list[ReplayEntry] = []

    def add(self, entry: ReplayEntry) -> None:
        self.items.append(entry)
        if len(self.items) > self.capacity:
            self.items = self.items[-self.capacity :]

    def freshness_window(self, recent_games: int, current_game_idx: int) -> list[ReplayEntry]:
        low = max(0, current_game_idx - recent_games)
        return [x for x in self.items if x.game_index >= low]


class SelfPlayPipeline:
    def __init__(self, workers: int = 4, seed: int = 42):
        self.workers = workers
        self.seed = seed
        self.engine = BaselineRuleEngine()
        self.agent = ShallowSearchAgent(depth=2)
        self.buffer = ReplayBuffer(capacity=10000)
        self.rng = random.Random(seed)

    def run_games(self, games: int = 100) -> dict[str, float]:
        t0 = time.time()
        for game_idx in range(games):
            state = self.engine.initial_state(seed=self.seed + game_idx)
            trajectory_hashes = []
            while not self.engine.is_terminal(state):
                legal = self.engine.legal_moves(state)
                move = self.agent.select_move(self.engine, state)
                trajectory_hashes.append(hash((state.side_to_move, state.ply, len(legal))))
                state = self.engine.apply_move(state, move)
            winner = self.engine.winner(state)
            value_target = float(winner)
            for h in trajectory_hashes:
                policy_target = [1.0]
                self.buffer.add(ReplayEntry(state_hash=h, policy_target=policy_target, value_target=value_target, game_index=game_idx))

        elapsed = max(time.time() - t0, 1e-9)
        gph = games * 3600.0 / elapsed
        fresh_items = self.buffer.freshness_window(recent_games=50, current_game_idx=games)
        return {
            "games": games,
            "elapsed_sec": elapsed,
            "games_per_hour": gph,
            "replay_size": float(len(self.buffer.items)),
            "fresh_window_size": float(len(fresh_items)),
        }
