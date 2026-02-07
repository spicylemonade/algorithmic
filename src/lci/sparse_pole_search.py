from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class PolePeriodSolution:
    lambda_deg: float
    beta_deg: float
    period_hours: float
    score: float
    mirror_retained: bool


class SparsePoleSearcher:
    """Coarse-to-fine sparse-only pole search with mirror ambiguity pruning."""

    def __init__(self, seed: int = 42):
        self.seed = seed

    def _grid(self, step: float):
        for lon in range(0, 360, int(step)):
            for lat in range(-90, 91, int(step)):
                yield float(lon), float(lat)

    def _period_grid(self, lo: float, hi: float, step: float):
        p = lo
        while p <= hi + 1e-12:
            yield round(p, 6)
            p += step

    def search(self, scorer, p_range=(2.0, 20.0)) -> PolePeriodSolution:
        best = (1e18, 0.0, 0.0, 0.0)
        for p in self._period_grid(p_range[0], p_range[1], 0.1):
            for lon, lat in self._grid(20):
                s = scorer(lon, lat, p)
                if s < best[0]:
                    best = (s, lon, lat, p)

        for step, p_step in [(10, 0.02), (5, 0.005), (2, 0.001)]:
            s0, lon0, lat0, p0 = best
            for p in self._period_grid(max(p_range[0], p0 - 0.1), min(p_range[1], p0 + 0.1), p_step):
                for dlon in range(-2 * step, 2 * step + 1, step):
                    for dlat in range(-2 * step, 2 * step + 1, step):
                        lon = (lon0 + dlon) % 360.0
                        lat = max(-90.0, min(90.0, lat0 + dlat))
                        s = scorer(lon, lat, p)
                        if s < best[0]:
                            best = (s, lon, lat, p)

        score, lon, lat, p = best
        mirror = scorer((lon + 180.0) % 360.0, -lat, p)
        keep_mirror = abs(mirror - score) < 0.015
        return PolePeriodSolution(lon, lat, p, score, keep_mirror)


def synthetic_sparse_scorer(true_lon, true_lat, true_p, noise=0.01):
    def _score(lon, lat, p):
        dlon = min(abs(lon - true_lon), 360 - abs(lon - true_lon))
        dlat = abs(lat - true_lat)
        dp = abs(p - true_p)
        return math.sqrt((dlon / 60.0) ** 2 + (dlat / 40.0) ** 2 + (dp / 0.2) ** 2) * 0.05 + noise

    return _score
