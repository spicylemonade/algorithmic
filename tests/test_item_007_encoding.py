#!/usr/bin/env python3
import json
import random
from pathlib import Path

from alphago5d.encoding import EncodingSpec, TensorCodec
from alphago5d.types import GameState, Move, Piece

PIECES = ["P", "N", "B", "R", "Q", "K"]


def random_state(rng: random.Random, spec: EncodingSpec) -> GameState:
    boards = {}
    for l in range(spec.max_timelines):
        for t in range(spec.max_times):
            if rng.random() < 0.45:
                continue
            board = {}
            for _ in range(rng.randint(1, 10)):
                sq = (rng.randint(0, 7), rng.randint(0, 7))
                if sq in board:
                    continue
                board[sq] = Piece(color=rng.choice(["W", "B"]), kind=rng.choice(PIECES))
            if board:
                boards[(l, t)] = board
    return GameState(boards=boards, active_player=rng.choice(["W", "B"]), max_timeline=spec.max_timelines - 1)


def random_move(rng: random.Random, spec: EncodingSpec) -> Move:
    promo = rng.choice([None, None, None, "Q", "N", "B", "R"])
    return Move(
        src_slice=(rng.randint(0, spec.max_timelines - 1), rng.randint(0, spec.max_times - 1)),
        dst_slice=(rng.randint(0, spec.max_timelines - 1), rng.randint(0, spec.max_times - 1)),
        src=(rng.randint(0, 7), rng.randint(0, 7)),
        dst=(rng.randint(0, 7), rng.randint(0, 7)),
        promotion=promo,
        creates_timeline=bool(rng.randint(0, 1)),
    )


def canonical_state(state: GameState):
    return (
        state.active_player,
        tuple(
            sorted(
                (
                    key,
                    tuple(sorted((sq, (p.color, p.kind)) for sq, p in board.items())),
                )
                for key, board in state.boards.items()
            )
        ),
    )


def run() -> dict:
    rng = random.Random(42)
    spec = EncodingSpec(max_timelines=4, max_times=4)
    codec = TensorCodec(spec)

    n_states = 10000
    n_actions = 10000
    state_mismatch = 0
    action_mismatch = 0

    for _ in range(n_states):
        s = random_state(rng, spec)
        d = codec.decode_state(codec.encode_state(s))
        if canonical_state(s) != canonical_state(d):
            state_mismatch += 1

    for _ in range(n_actions):
        a = random_move(rng, spec)
        b = codec.decode_action(codec.encode_action(a))
        if a != b:
            action_mismatch += 1

    report = {
        "item_id": "item_007",
        "seed": 42,
        "state_roundtrip_tests": n_states,
        "action_roundtrip_tests": n_actions,
        "state_mismatches": state_mismatch,
        "action_mismatches": action_mismatch,
        "total_mismatches": state_mismatch + action_mismatch,
        "passed": state_mismatch == 0 and action_mismatch == 0,
        "tensor_schema": {
            "shape": [spec.max_timelines, spec.max_times, spec.rows, spec.cols, spec.channels],
            "description": "[timeline,time,rank,file,channel] with channels=12 piece planes + side_to_move + occupancy"
        },
        "action_indexing": "mixed-radix packing over (src_l,src_t,src_r,src_c,dst_l,dst_t,dst_r,dst_c,promo,branch)",
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/item_007_encoding_roundtrip.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    report = run()
    assert report["passed"], report
    print(json.dumps({k: report[k] for k in ["state_roundtrip_tests", "action_roundtrip_tests", "total_mismatches", "passed"]}, indent=2))
