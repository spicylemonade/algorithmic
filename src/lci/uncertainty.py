from __future__ import annotations

import numpy as np


def confidence_interval(samples: np.ndarray, alpha: float = 0.95) -> tuple[float, float]:
    lo = (1 - alpha) / 2
    hi = 1 - lo
    return float(np.quantile(samples, lo)), float(np.quantile(samples, hi))


def bootstrap_multistart(estimator_fn, data, n_boot: int = 200, seed: int = 42):
    rng = np.random.default_rng(seed)
    samples = []
    n = len(data)
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        subset = [data[i] for i in idx]
        samples.append(estimator_fn(subset, rng))
    return np.array(samples)
