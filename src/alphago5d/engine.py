from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .contracts import Move


PIECE_VALUE = {"P": 1, "N": 3, "K": 100}


@dataclass(frozen=True)
class Piece:
    kind: str
    color: int  # 1 white, -1 black


@dataclass
class BaselineState:
    board: list[list[Piece | None]]
    side_to_move: int
    ply: int = 0


class BaselineRuleEngine:
    """Deterministic baseline move generator over a simplified board slice."""

    def __init__(self) -> None:
        self.size = 8

    def clone(self, state: BaselineState) -> BaselineState:
        return BaselineState(
            board=[[cell for cell in row] for row in state.board],
            side_to_move=state.side_to_move,
            ply=state.ply,
        )

    def initial_state(self, seed: int = 42) -> BaselineState:
        board = [[None for _ in range(self.size)] for _ in range(self.size)]
        board[0][4] = Piece("K", 1)
        board[7][4] = Piece("K", -1)
        board[0][1] = Piece("N", 1)
        board[7][6] = Piece("N", -1)
        board[1][0] = Piece("P", 1)
        board[6][0] = Piece("P", -1)
        return BaselineState(board=board, side_to_move=1, ply=0)

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
            step = 1 if piece.color == 1 else -1
            nr = r + step
            if self._inside(nr, c) and state.board[nr][c] is None:
                moves.append(Move(0, 0, src_sq, 0, 0, nr * 8 + c))
            for dc in (-1, 1):
                nc = c + dc
                if self._inside(nr, nc):
                    target = state.board[nr][nc]
                    if target is not None and target.color != piece.color:
                        moves.append(Move(0, 0, src_sq, 0, 0, nr * 8 + nc))

        return sorted(moves, key=lambda m: (m.dst_square, m.src_square))

    def legal_moves(self, state: BaselineState) -> list[Move]:
        all_moves: list[Move] = []
        for r in range(self.size):
            for c in range(self.size):
                all_moves.extend(self._iter_piece_moves(state, r, c))
        return sorted(all_moves, key=lambda m: (m.src_square, m.dst_square))

    def apply_move(self, state: BaselineState, move: Move) -> BaselineState:
        src_r, src_c = divmod(move.src_square, 8)
        dst_r, dst_c = divmod(move.dst_square, 8)
        piece = state.board[src_r][src_c]
        if piece is None:
            raise RuntimeError("No piece at source square")
        next_state = self.clone(state)
        next_state.board[dst_r][dst_c] = piece
        next_state.board[src_r][src_c] = None
        next_state.side_to_move = -state.side_to_move
        next_state.ply = state.ply + 1
        return next_state

    def material_score(self, state: BaselineState, color: int) -> int:
        score = 0
        for row in state.board:
            for piece in row:
                if piece is None:
                    continue
                val = PIECE_VALUE[piece.kind]
                score += val if piece.color == color else -val
        return score

    def is_terminal(self, state: BaselineState, max_ply: int = 40) -> bool:
        white_king = any(piece is not None and piece.kind == "K" and piece.color == 1 for row in state.board for piece in row)
        black_king = any(piece is not None and piece.kind == "K" and piece.color == -1 for row in state.board for piece in row)
        if not white_king or not black_king:
            return True
        if state.ply >= max_ply:
            return True
        if not self.legal_moves(state):
            return True
        return False

    def winner(self, state: BaselineState) -> int:
        white_king = any(piece is not None and piece.kind == "K" and piece.color == 1 for row in state.board for piece in row)
        black_king = any(piece is not None and piece.kind == "K" and piece.color == -1 for row in state.board for piece in row)
        if white_king and not black_king:
            return 1
        if black_king and not white_king:
            return -1
        mat = self.material_score(state, 1)
        if mat > 0:
            return 1
        if mat < 0:
            return -1
        return 0
