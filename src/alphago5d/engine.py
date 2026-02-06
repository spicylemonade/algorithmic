from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Iterable, List, Set, Tuple

from .types import GameState, Move, Piece, SliceKey, Square


DIRS_KING = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]
DIRS_ROOK = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DIRS_BISHOP = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
KNIGHT_OFFSETS = [
    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    (1, -2), (1, 2), (2, -1), (2, 1),
]


class GameEngine5D:
    """Deterministic 5D chess-like engine API for research prototyping."""

    def legal_moves(self, state: GameState) -> List[Move]:
        return sorted(
            self._legal_moves_impl(state),
            key=lambda m: (m.src_slice, m.dst_slice, m.src, m.dst, m.promotion or "", m.creates_timeline),
        )

    def legal_moves_reference(self, state: GameState) -> List[Move]:
        """Independent implementation used as correctness oracle."""
        moves: Set[Tuple] = set()
        for sl in self._present_slices(state.boards):
            board = state.boards[sl]
            for src, pc in board.items():
                if pc.color != state.active_player:
                    continue
                for dst, promo in self._piece_dests_reference(pc, src, board):
                    if self._in_bounds(dst) and not self._friendly_occupied(board, dst, pc.color):
                        moves.add((sl, sl, src, dst, promo, False))
                # Optional time-travel edge
                t = sl[1]
                back_key = (sl[0], t - 1)
                if pc.kind in {"N", "B", "R", "Q"} and back_key in state.boards:
                    for dst in self._time_jump_targets(src):
                        if self._in_bounds(dst) and not self._friendly_occupied(state.boards[back_key], dst, pc.color):
                            moves.add((sl, back_key, src, dst, None, True))
        return [
            Move(src_slice=a, dst_slice=b, src=c, dst=d, promotion=e, creates_timeline=f)
            for (a, b, c, d, e, f) in sorted(moves)
        ]

    def apply(self, state: GameState, move: Move) -> GameState:
        nxt = state.clone()
        src_board = nxt.boards[move.src_slice]
        piece = src_board.pop(move.src)
        dst_key = move.dst_slice
        if move.creates_timeline and dst_key[1] < move.src_slice[1]:
            nxt.max_timeline += 1
            dst_key = (nxt.max_timeline, dst_key[1])
            nxt.boards[dst_key] = dict(nxt.boards[move.dst_slice])
        dst_board = nxt.boards[dst_key]
        dst_board.pop(move.dst, None)
        if move.promotion:
            piece = Piece(color=piece.color, kind=move.promotion)
        dst_board[move.dst] = piece
        nxt.active_player = "B" if state.active_player == "W" else "W"
        return nxt

    def state_to_dict(self, state: GameState) -> Dict:
        return {
            "boards": {
                f"{k[0]}:{k[1]}": {
                    f"{sq[0]},{sq[1]}": asdict(pc) for sq, pc in sorted(v.items())
                }
                for k, v in sorted(state.boards.items())
            },
            "active_player": state.active_player,
            "max_timeline": state.max_timeline,
        }

    def _legal_moves_impl(self, state: GameState) -> List[Move]:
        out: List[Move] = []
        for sl in self._present_slices(state.boards):
            board = state.boards[sl]
            for src, piece in board.items():
                if piece.color != state.active_player:
                    continue
                for dst, promo in self._piece_dests(piece, src, board):
                    if self._in_bounds(dst) and not self._friendly_occupied(board, dst, piece.color):
                        out.append(Move(sl, sl, src, dst, promo, False))
                back_key = (sl[0], sl[1] - 1)
                if piece.kind in {"N", "B", "R", "Q"} and back_key in state.boards:
                    back_board = state.boards[back_key]
                    for dst in self._time_jump_targets(src):
                        if self._in_bounds(dst) and not self._friendly_occupied(back_board, dst, piece.color):
                            out.append(Move(sl, back_key, src, dst, None, True))
        return out

    def _piece_dests(self, p: Piece, src: Square, board: Dict[Square, Piece]) -> Iterable[Tuple[Square, str | None]]:
        r, c = src
        if p.kind == "K":
            for dr, dc in DIRS_KING:
                yield (r + dr, c + dc), None
        elif p.kind == "N":
            for dr, dc in KNIGHT_OFFSETS:
                yield (r + dr, c + dc), None
        elif p.kind in {"B", "R", "Q"}:
            dirs = []
            if p.kind in {"B", "Q"}:
                dirs.extend(DIRS_BISHOP)
            if p.kind in {"R", "Q"}:
                dirs.extend(DIRS_ROOK)
            for dr, dc in dirs:
                rr, cc = r + dr, c + dc
                while self._in_bounds((rr, cc)):
                    yield (rr, cc), None
                    if (rr, cc) in board:
                        break
                    rr += dr
                    cc += dc
        elif p.kind == "P":
            step = 1 if p.color == "W" else -1
            one = (r + step, c)
            if self._in_bounds(one) and one not in board:
                promo = "Q" if one[0] in {0, 7} else None
                yield one, promo
            for dc in (-1, 1):
                cap = (r + step, c + dc)
                if self._in_bounds(cap) and cap in board and board[cap].color != p.color:
                    promo = "Q" if cap[0] in {0, 7} else None
                    yield cap, promo

    def _piece_dests_reference(self, p: Piece, src: Square, board: Dict[Square, Piece]) -> List[Tuple[Square, str | None]]:
        # Kept intentionally separate from _piece_dests for regression cross-checking.
        rr, cc = src
        out: List[Tuple[Square, str | None]] = []
        if p.kind == "K":
            for dr, dc in DIRS_KING:
                out.append(((rr + dr, cc + dc), None))
        elif p.kind == "N":
            for dr, dc in KNIGHT_OFFSETS:
                out.append(((rr + dr, cc + dc), None))
        elif p.kind in {"B", "R", "Q"}:
            sweep = []
            if p.kind != "R":
                sweep += DIRS_BISHOP
            if p.kind != "B":
                sweep += DIRS_ROOK
            for dr, dc in sweep:
                r2, c2 = rr + dr, cc + dc
                while 0 <= r2 < 8 and 0 <= c2 < 8:
                    out.append(((r2, c2), None))
                    if (r2, c2) in board:
                        break
                    r2 += dr
                    c2 += dc
        elif p.kind == "P":
            step = 1 if p.color == "W" else -1
            target = (rr + step, cc)
            if 0 <= target[0] < 8 and 0 <= target[1] < 8 and target not in board:
                out.append((target, "Q" if target[0] in {0, 7} else None))
            for dc in (-1, 1):
                cap = (rr + step, cc + dc)
                if 0 <= cap[0] < 8 and 0 <= cap[1] < 8 and cap in board and board[cap].color != p.color:
                    out.append((cap, "Q" if cap[0] in {0, 7} else None))
        return out

    def _present_slices(self, boards: Dict[SliceKey, Dict[Square, Piece]]) -> List[SliceKey]:
        max_by_timeline: Dict[int, int] = {}
        for l, t in boards:
            max_by_timeline[l] = max(max_by_timeline.get(l, -10**9), t)
        return sorted((l, t) for l, t in boards if t == max_by_timeline[l])

    @staticmethod
    def _in_bounds(sq: Square) -> bool:
        return 0 <= sq[0] < 8 and 0 <= sq[1] < 8

    @staticmethod
    def _friendly_occupied(board: Dict[Square, Piece], sq: Square, color: str) -> bool:
        return sq in board and board[sq].color == color

    @staticmethod
    def _time_jump_targets(src: Square) -> List[Square]:
        r, c = src
        return [(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
