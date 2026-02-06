from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .types import GameState, Move, Piece, SliceKey, Square

PIECE_TO_CHANNEL = {
    ("W", "P"): 0,
    ("W", "N"): 1,
    ("W", "B"): 2,
    ("W", "R"): 3,
    ("W", "Q"): 4,
    ("W", "K"): 5,
    ("B", "P"): 6,
    ("B", "N"): 7,
    ("B", "B"): 8,
    ("B", "R"): 9,
    ("B", "Q"): 10,
    ("B", "K"): 11,
}
CHANNEL_TO_PIECE = {v: k for k, v in PIECE_TO_CHANNEL.items()}


@dataclass(frozen=True)
class EncodingSpec:
    max_timelines: int = 4
    max_times: int = 4
    rows: int = 8
    cols: int = 8
    channels: int = 14


class TensorCodec:
    """Sparse tensor codec with explicit shape metadata for reproducible encoding."""

    def __init__(self, spec: EncodingSpec | None = None):
        self.spec = spec or EncodingSpec()

    def encode_state(self, state: GameState) -> Dict:
        s = self.spec
        entries: List[Tuple[int, int, int, int, int]] = []
        for (l, t), board in state.boards.items():
            if not (0 <= l < s.max_timelines and 0 <= t < s.max_times):
                continue
            for (r, c), p in board.items():
                entries.append((l, t, r, c, PIECE_TO_CHANNEL[(p.color, p.kind)]))
                entries.append((l, t, r, c, 13))
        if state.active_player == "W":
            entries.append((0, 0, 0, 0, 12))
        return {
            "shape": [s.max_timelines, s.max_times, s.rows, s.cols, s.channels],
            "sparse_entries": sorted(entries),
        }

    def decode_state(self, tensor: Dict) -> GameState:
        s = self.spec
        assert tensor["shape"] == [s.max_timelines, s.max_times, s.rows, s.cols, s.channels]
        boards: Dict[SliceKey, Dict[Square, Piece]] = {}
        active_player = "B"
        for l, t, r, c, ch in tensor["sparse_entries"]:
            if ch == 12:
                active_player = "W"
                continue
            if ch >= 12:
                continue
            color, kind = CHANNEL_TO_PIECE[ch]
            key = (l, t)
            if key not in boards:
                boards[key] = {}
            boards[key][(r, c)] = Piece(color=color, kind=kind)
        max_timeline = max((k[0] for k in boards), default=0)
        return GameState(boards=boards, active_player=active_player, max_timeline=max_timeline)

    def encode_action(self, move: Move) -> int:
        s = self.spec
        promo_code = {None: 0, "N": 1, "B": 2, "R": 3, "Q": 4}[move.promotion]
        idx = 0
        fields = [
            (move.src_slice[0], s.max_timelines),
            (move.src_slice[1], s.max_times),
            (move.src[0], s.rows),
            (move.src[1], s.cols),
            (move.dst_slice[0], s.max_timelines),
            (move.dst_slice[1], s.max_times),
            (move.dst[0], s.rows),
            (move.dst[1], s.cols),
            (promo_code, 5),
            (1 if move.creates_timeline else 0, 2),
        ]
        for value, radix in fields:
            idx = idx * radix + value
        return idx

    def decode_action(self, idx: int) -> Move:
        s = self.spec
        radices = [s.max_timelines, s.max_times, s.rows, s.cols, s.max_timelines, s.max_times, s.rows, s.cols, 5, 2]
        vals: List[int] = []
        cur = idx
        for radix in reversed(radices):
            vals.append(cur % radix)
            cur //= radix
        vals = list(reversed(vals))
        promo = {0: None, 1: "N", 2: "B", 3: "R", 4: "Q"}[vals[8]]
        return Move(
            src_slice=(vals[0], vals[1]),
            dst_slice=(vals[4], vals[5]),
            src=(vals[2], vals[3]),
            dst=(vals[6], vals[7]),
            promotion=promo,
            creates_timeline=bool(vals[9]),
        )
