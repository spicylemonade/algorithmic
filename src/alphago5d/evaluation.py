from __future__ import annotations

import random
from dataclasses import dataclass

from .engine import BaselineRuleEngine


@dataclass
class MatchResult:
    games: int
    wins_a: int
    wins_b: int
    draws: int


def play_match(agent_a, agent_b, games: int, seed: int = 42) -> MatchResult:
    rng = random.Random(seed)
    engine = BaselineRuleEngine()
    wins_a = 0
    wins_b = 0
    draws = 0

    for i in range(games):
        state = engine.initial_state(seed=seed + i)
        agents = {1: agent_a, -1: agent_b}
        if i % 2 == 1:
            agents = {1: agent_b, -1: agent_a}
        while not engine.is_terminal(state):
            move = agents[state.side_to_move].select_move(engine, state)
            state = engine.apply_move(state, move)
        winner = engine.winner(state)
        if winner == 0:
            draws += 1
        else:
            white_is_a = (i % 2 == 0)
            a_won = (winner == 1 and white_is_a) or (winner == -1 and not white_is_a)
            if a_won:
                wins_a += 1
            else:
                wins_b += 1

    return MatchResult(games=games, wins_a=wins_a, wins_b=wins_b, draws=draws)
