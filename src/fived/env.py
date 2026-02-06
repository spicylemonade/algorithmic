from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import copy
import random

BOARD_SIZE = 4
DIRECTIONS_KING = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
DIRECTIONS_ROOK = [(-1, 0), (1, 0), (0, -1), (0, 1)]
KNIGHT_STEPS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]


@dataclass(frozen=True)
class Action:
    src_timeline: int
    src_time: int
    src_row: int
    src_col: int
    dst_timeline: int
    dst_time: int
    dst_row: int
    dst_col: int
    promotion: str = ""


class FiveDChessEnv:
    """A compact, deterministic timeline-chess environment suitable for research loops.

    This is not a full commercial 5D Chess ruleset. It is a deterministic approximation with
    timeline branching and temporal moves designed for AlphaGo-style research workflows.
    """

    def __init__(self, max_moves: int = 60):
        self.max_moves = max_moves
        self.rng = random.Random(42)
        self.reset(seed=42)

    def reset(self, seed: int = 42) -> dict:
        self.rng = random.Random(seed)
        self.seed = seed
        self.move_count = 0
        self.side_to_move = "W"
        self.next_timeline_id = 1
        self.done = False

        board = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        # White
        board[3][0] = "R"
        board[3][3] = "K"
        board[2][1] = "P"
        # Black
        board[0][3] = "r"
        board[0][0] = "k"
        board[1][2] = "p"

        # Seed-controlled deterministic opening variation.
        if self.rng.random() < 0.5:
            board[3][0], board[3][2] = ".", "R"
            board[0][3], board[0][1] = ".", "r"

        self.boards: Dict[Tuple[int, int], List[List[str]]] = {(0, 0): board}
        self.timeline_latest: Dict[int, int] = {0: 0}
        return self._observation()

    def _observation(self) -> dict:
        return {
            "boards": copy.deepcopy(self.boards),
            "timeline_latest": dict(self.timeline_latest),
            "side_to_move": self.side_to_move,
            "move_count": self.move_count,
            "done": self.done,
        }

    def _in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def _is_white(self, piece: str) -> bool:
        return piece.isupper()

    def _is_black(self, piece: str) -> bool:
        return piece.islower()

    def _belongs_to_side(self, piece: str) -> bool:
        if piece == ".":
            return False
        return self._is_white(piece) if self.side_to_move == "W" else self._is_black(piece)

    def _enemy(self, piece: str) -> bool:
        if piece == ".":
            return False
        return self._is_black(piece) if self.side_to_move == "W" else self._is_white(piece)

    def _frontier_nodes(self) -> List[Tuple[int, int]]:
        return sorted((tl, t) for tl, t in self.timeline_latest.items())

    def legal_actions(self) -> List[Action]:
        if self.done:
            return []

        actions: List[Action] = []
        for tl, tm in self._frontier_nodes():
            board = self.boards[(tl, tm)]
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    piece = board[r][c]
                    if not self._belongs_to_side(piece):
                        continue
                    actions.extend(self._piece_moves(tl, tm, r, c, piece, board))
                    # Temporal move: non-king can branch to previous time in same timeline.
                    if piece.upper() != "K" and tm > 0:
                        prev_tm = tm - 1
                        if (tl, prev_tm) not in self.boards:
                            continue
                        target_board = self.boards[(tl, prev_tm)]
                        if target_board[r][c] == piece:
                            for rr in range(BOARD_SIZE):
                                for cc in range(BOARD_SIZE):
                                    dst_piece = target_board[rr][cc]
                                    if (rr, cc) != (r, c) and (dst_piece == "." or self._enemy(dst_piece)):
                                        actions.append(
                                            Action(tl, tm, r, c, tl, prev_tm, rr, cc)
                                        )
        return actions

    def _piece_moves(self, tl: int, tm: int, r: int, c: int, piece: str, board: List[List[str]]) -> List[Action]:
        out: List[Action] = []
        p = piece.upper()
        if p == "K":
            for dr, dc in DIRECTIONS_KING:
                rr, cc = r + dr, c + dc
                if self._in_bounds(rr, cc):
                    dst = board[rr][cc]
                    if dst == "." or self._enemy(dst):
                        out.append(Action(tl, tm, r, c, tl, tm, rr, cc))
        elif p == "R":
            for dr, dc in DIRECTIONS_ROOK:
                rr, cc = r + dr, c + dc
                while self._in_bounds(rr, cc):
                    dst = board[rr][cc]
                    if dst == ".":
                        out.append(Action(tl, tm, r, c, tl, tm, rr, cc))
                    elif self._enemy(dst):
                        out.append(Action(tl, tm, r, c, tl, tm, rr, cc))
                        break
                    else:
                        break
                    rr += dr
                    cc += dc
        elif p == "N":
            for dr, dc in KNIGHT_STEPS:
                rr, cc = r + dr, c + dc
                if self._in_bounds(rr, cc):
                    dst = board[rr][cc]
                    if dst == "." or self._enemy(dst):
                        out.append(Action(tl, tm, r, c, tl, tm, rr, cc))
        elif p == "P":
            step = -1 if piece.isupper() else 1
            rr, cc = r + step, c
            if self._in_bounds(rr, cc) and board[rr][cc] == ".":
                out.append(Action(tl, tm, r, c, tl, tm, rr, cc))
            for dc in (-1, 1):
                rr, cc = r + step, c + dc
                if self._in_bounds(rr, cc) and self._enemy(board[rr][cc]):
                    out.append(Action(tl, tm, r, c, tl, tm, rr, cc))
        return out

    def is_terminal(self) -> bool:
        if self.done:
            return True
        kings = {"K": 0, "k": 0}
        for b in self.boards.values():
            for row in b:
                for piece in row:
                    if piece in kings:
                        kings[piece] += 1
        if kings["K"] == 0 or kings["k"] == 0:
            return True
        if self.move_count >= self.max_moves:
            return True
        if len(self.legal_actions()) == 0:
            return True
        return False

    def _winner(self) -> int:
        # Reward from White perspective.
        kings = {"K": 0, "k": 0}
        for b in self.boards.values():
            for row in b:
                for piece in row:
                    if piece in kings:
                        kings[piece] += 1
        if kings["k"] == 0 and kings["K"] > 0:
            return 1
        if kings["K"] == 0 and kings["k"] > 0:
            return -1
        return 0

    def _apply_spatial(self, action: Action) -> None:
        src_key = (action.src_timeline, action.src_time)
        src_board = copy.deepcopy(self.boards[src_key])
        piece = src_board[action.src_row][action.src_col]
        src_board[action.src_row][action.src_col] = "."
        src_board[action.dst_row][action.dst_col] = piece if not action.promotion else action.promotion
        next_time = self.timeline_latest[action.src_timeline] + 1
        self.boards[(action.src_timeline, next_time)] = src_board
        self.timeline_latest[action.src_timeline] = next_time

    def _apply_temporal(self, action: Action) -> None:
        target_key = (action.dst_timeline, action.dst_time)
        base_board = copy.deepcopy(self.boards[target_key])
        piece = base_board[action.src_row][action.src_col]
        base_board[action.src_row][action.src_col] = "."
        base_board[action.dst_row][action.dst_col] = piece

        new_tl = self.next_timeline_id
        self.next_timeline_id += 1
        self.boards[(new_tl, action.dst_time + 1)] = base_board
        self.timeline_latest[new_tl] = action.dst_time + 1

    def step(self, action: Action) -> Tuple[dict, float, bool, dict]:
        if self.done:
            raise RuntimeError("Cannot step after terminal state")

        legal = self.legal_actions()
        if action not in legal:
            raise ValueError("Illegal action")

        is_temporal = action.src_time != action.dst_time
        if is_temporal:
            self._apply_temporal(action)
        else:
            self._apply_spatial(action)

        self.move_count += 1
        self.side_to_move = "B" if self.side_to_move == "W" else "W"
        self.done = self.is_terminal()
        reward = float(self._winner()) if self.done else 0.0
        info = {"temporal": is_temporal, "legal_action_count": len(legal)}
        return self._observation(), reward, self.done, info
