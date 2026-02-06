from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .contracts import Move


@dataclass(frozen=True)
class Piece:
    kind: str
    color: int  # 1 white, -1 black


@dataclass
class BaselineState:
    board: list[list[Piece | None]]
    side_to_move: int


class BaselineRuleEngine:
    """Deterministic baseline move generator over a simplified board slice."""

    def __init__(self) -> None:
        self.size = 8

    def initial_state(self, seed: int = 42) -> BaselineState:
        board = [[None for _ in range(self.size)] for _ in range(self.size)]
        board[0][4] = Piece("K", 1)
        board[7][4] = Piece("K", -1)
        board[0][1] = Piece("N", 1)
        board[6][0] = Piece("P", -1)
        return BaselineState(board=board, side_to_move=1)

    def _inside(self, r: int, c: int) -> bool:
        return 0 <= r < self.size and 0 <= c < self.size

    def _iter_piece_moves(self, state: BaselineState, r: int, c: int) -> Iterable[Move]:
        piece = state.board[r][c]
        if piece is None or piece.color != state.side_to_move:
            return []

        moves: list[Move] = []
        src_sq = r * 8 + c

        if piece.kind == "N":
            for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                nr, nc = r + dr, c + dc
                if not self._inside(nr, nc):
                    continue
                target = state.board[nr][nc]
                if target is None or target.color != piece.color:
                    moves.append(Move(0, 0, src_sq, 0, 0, nr * 8 + nc))

        if piece.kind == "K":
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if not self._inside(nr, nc):
                        continue
                    target = state.board[nr][nc]
                    if target is None or target.color != piece.color:
                        moves.append(Move(0, 0, src_sq, 0, 0, nr * 8 + nc))

        if piece.kind == "P":
            step = -1 if piece.color == 1 else 1
            nr = r + step
            if self._inside(nr, c) and state.board[nr][c] is None:
                moves.append(Move(0, 0, src_sq, 0, 0, nr * 8 + c))

        # Deterministic ordering for reproducibility.
        return sorted(moves, key=lambda m: (m.dst_square, m.src_square))

    def legal_moves(self, state: BaselineState) -> list[Move]:
        all_moves: list[Move] = []
        for r in range(self.size):
            for c in range(self.size):
                all_moves.extend(self._iter_piece_moves(state, r, c))
        return sorted(all_moves, key=lambda m: (m.src_square, m.dst_square))
