from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from .env import Action, BOARD_SIZE

PIECES = ["P", "R", "N", "B", "Q", "K", "p", "r", "n", "b", "q", "k"]
PIECE_TO_CH = {p: i for i, p in enumerate(PIECES)}
CH_TO_PIECE = {i: p for i, p in enumerate(PIECES)}


@dataclass
class TensorState:
    tensor: np.ndarray
    timeline_ids: List[int]
    time_ids: List[int]
    side_to_move: str


class StateSchema:
    def __init__(self, max_timelines: int = 8, max_time: int = 16):
        self.max_timelines = max_timelines
        self.max_time = max_time
        self.channels = len(PIECES) + 1

    def encode(self, obs: dict) -> TensorState:
        tensor = np.zeros((self.max_timelines, self.max_time, BOARD_SIZE, BOARD_SIZE, self.channels), dtype=np.int8)
        timeline_ids = sorted(obs["timeline_latest"].keys())[: self.max_timelines]
        max_seen_time = 0
        for i, tl in enumerate(timeline_ids):
            for tm in range(obs["timeline_latest"][tl] + 1):
                if tm >= self.max_time:
                    break
                if (tl, tm) not in obs["boards"]:
                    continue
                max_seen_time = max(max_seen_time, tm)
                board = obs["boards"][(tl, tm)]
                for r in range(BOARD_SIZE):
                    for c in range(BOARD_SIZE):
                        piece = board[r][c]
                        if piece in PIECE_TO_CH:
                            tensor[i, tm, r, c, PIECE_TO_CH[piece]] = 1
                tensor[i, tm, :, :, -1] = 1 if obs["side_to_move"] == "W" else 0
        time_ids = list(range(max_seen_time + 1))
        return TensorState(tensor=tensor, timeline_ids=timeline_ids, time_ids=time_ids, side_to_move=obs["side_to_move"])

    def decode(self, state: TensorState) -> dict:
        boards: Dict[Tuple[int, int], List[List[str]]] = {}
        timeline_latest: Dict[int, int] = {}
        for i, tl in enumerate(state.timeline_ids):
            latest = -1
            for tm in state.time_ids:
                board = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
                any_piece = False
                for r in range(BOARD_SIZE):
                    for c in range(BOARD_SIZE):
                        ch = int(np.argmax(state.tensor[i, tm, r, c, :-1]))
                        if state.tensor[i, tm, r, c, ch] == 1:
                            board[r][c] = CH_TO_PIECE[ch]
                            any_piece = True
                if any_piece:
                    boards[(tl, tm)] = board
                    latest = tm
            if latest >= 0:
                timeline_latest[tl] = latest
        return {
            "boards": boards,
            "timeline_latest": timeline_latest,
            "side_to_move": state.side_to_move,
            "move_count": 0,
            "done": False,
        }


def encode_action(action: Action) -> List[int]:
    return [
        action.src_timeline,
        action.src_time,
        action.src_row,
        action.src_col,
        action.dst_timeline,
        action.dst_time,
        action.dst_row,
        action.dst_col,
    ]


def decode_action(v: List[int]) -> Action:
    return Action(v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7])


def save_replay(path: str | Path, samples: List[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in samples:
            f.write(json.dumps(row) + "\n")


def load_replay(path: str | Path) -> List[dict]:
    rows = []
    with Path(path).open() as f:
        for line in f:
            rows.append(json.loads(line))
    return rows
