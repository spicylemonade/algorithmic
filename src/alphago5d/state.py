from __future__ import annotations

from dataclasses import dataclass
import random

Tensor5D = list[list[list[list[list[int]]]]]


@dataclass(frozen=True)
class GameState:
    boards: Tensor5D  # shape: (timelines, time, channels, 8, 8)
    side_to_move: int
    halfmove_clock: int
    fullmove_number: int


def sample_state(rng: random.Random, timelines: int = 2, times: int = 3, channels: int = 16) -> GameState:
    boards: Tensor5D = []
    for _ in range(timelines):
        timeline = []
        for _ in range(times):
            tstep = []
            for _ in range(channels):
                plane = [[rng.randint(-1, 1) for _ in range(8)] for _ in range(8)]
                tstep.append(plane)
            timeline.append(tstep)
        boards.append(timeline)

    return GameState(
        boards=boards,
        side_to_move=rng.randint(0, 1),
        halfmove_clock=rng.randint(0, 50),
        fullmove_number=rng.randint(1, 200),
    )
