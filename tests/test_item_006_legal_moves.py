#!/usr/bin/env python3
import json
import random
from pathlib import Path

from alphago5d.engine import GameEngine5D
from alphago5d.types import GameState, Piece


PIECES = ["P", "N", "B", "R", "Q", "K"]


def random_state(rng: random.Random) -> GameState:
    boards = {}
    timelines = [0, 1]
    for l in timelines:
        for t in range(2):
            board = {}
            n = rng.randint(6, 16)
            for _ in range(n):
                sq = (rng.randint(0, 7), rng.randint(0, 7))
                if sq in board:
                    continue
                board[sq] = Piece(color=rng.choice(["W", "B"]), kind=rng.choice(PIECES))
            boards[(l, t)] = board
    return GameState(boards=boards, active_player=rng.choice(["W", "B"]), max_timeline=1)


def move_key(m):
    return (m.src_slice, m.dst_slice, m.src, m.dst, m.promotion, m.creates_timeline)


def run() -> dict:
    rng = random.Random(42)
    engine = GameEngine5D()
    positions = []
    mismatches = 0
    total = 220
    for idx in range(total):
        st = random_state(rng)
        fast = {move_key(m) for m in engine.legal_moves(st)}
        ref = {move_key(m) for m in engine.legal_moves_reference(st)}
        ok = fast == ref
        mismatches += 0 if ok else 1
        positions.append(
            {
                "index": idx,
                "fast_count": len(fast),
                "ref_count": len(ref),
                "match": ok,
            }
        )

    agreement = (total - mismatches) / total
    out = {
        "item_id": "item_006",
        "seed": 42,
        "positions_tested": total,
        "mismatches": mismatches,
        "agreement": agreement,
        "pass_threshold": 0.995,
        "passed": agreement >= 0.995,
        "positions": positions,
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/item_006_legal_move_regression.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    report = run()
    assert report["passed"], f"Agreement below threshold: {report['agreement']:.4f}"
    print(json.dumps({k: report[k] for k in ['positions_tested','mismatches','agreement','passed']}, indent=2))
