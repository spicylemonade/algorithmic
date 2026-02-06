from __future__ import annotations

import math


def factorized_action_size(timelines: int = 2, times: int = 3, squares: int = 64) -> dict[str, int]:
    return {
        "src_timeline": timelines,
        "src_time": times,
        "src_square": squares,
        "dst_timeline": timelines,
        "dst_time": times,
        "dst_square": squares,
        "promotion": 5,
    }


def masked_softmax(logits: list[float], legal_mask: list[int]) -> list[float]:
    if len(logits) != len(legal_mask):
        raise ValueError("logits and legal_mask length mismatch")

    masked = [logit if legal_mask[i] else -1e9 for i, logit in enumerate(logits)]
    m = max(masked)
    exps = [0.0 if legal_mask[i] == 0 else math.exp(masked[i] - m) for i in range(len(masked))]
    z = sum(exps)
    if z <= 0:
        return [0.0] * len(logits)
    probs = [v / z for v in exps]

    for i, is_legal in enumerate(legal_mask):
        if not is_legal:
            probs[i] = 0.0
    return probs
