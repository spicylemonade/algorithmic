from __future__ import annotations

import numpy as np


def adaptive_weights(n_dense: int, n_sparse: int) -> tuple[float, float]:
    total = max(n_dense + n_sparse, 1)
    frac_sparse = n_sparse / total
    # Increase sparse influence as sparse fraction rises.
    w_sparse = 1.0 + 1.6 * frac_sparse
    w_dense = 1.0 - 0.25 * frac_sparse
    return float(w_dense), float(w_sparse)


def weighted_mse(dense_resid: np.ndarray, sparse_resid: np.ndarray, w_dense: float, w_sparse: float) -> float:
    d = np.mean(dense_resid ** 2) if dense_resid.size else 0.0
    s = np.mean(sparse_resid ** 2) if sparse_resid.size else 0.0
    return float(w_dense * d + w_sparse * s)
