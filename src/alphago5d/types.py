from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

Square = Tuple[int, int]
SliceKey = Tuple[int, int]  # (timeline, time_index)


@dataclass(frozen=True)
class Piece:
    color: str  # "W" or "B"
    kind: str   # "P", "N", "B", "R", "Q", "K"


@dataclass(frozen=True)
class Move:
    src_slice: SliceKey
    dst_slice: SliceKey
    src: Square
    dst: Square
    promotion: str | None = None
    creates_timeline: bool = False


@dataclass
class GameState:
    boards: Dict[SliceKey, Dict[Square, Piece]]
    active_player: str
    max_timeline: int = 0

    def clone(self) -> "GameState":
        return GameState(
            boards={k: dict(v) for k, v in self.boards.items()},
            active_player=self.active_player,
            max_timeline=self.max_timeline,
        )
