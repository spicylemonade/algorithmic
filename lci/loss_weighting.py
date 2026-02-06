"""Adaptive loss weighting for mixed dense/sparse photometry."""

from __future__ import annotations


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def compute_weight(sigma: float, phase_span_deg: float, apparitions: int) -> float:
    # w = (1/sigma^2) * f_phase * f_app, bounded to prevent domination.
    base = 1.0 / max(sigma * sigma, 1e-6)
    f_phase = clamp(phase_span_deg / 40.0, 0.25, 1.5)
    f_app = clamp(apparitions / 4.0, 0.3, 1.4)
    return clamp(base * f_phase * f_app, 0.1, 50.0)


def split_dense_sparse_weights(dense_sigma: float, sparse_sigma: float, phase_span_deg: float, apparitions: int):
    wd = compute_weight(dense_sigma, phase_span_deg, apparitions)
    ws = compute_weight(sparse_sigma, phase_span_deg, apparitions)
    total = wd + ws
    return {"w_dense": wd / total, "w_sparse": ws / total}
