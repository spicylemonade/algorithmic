from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass
class CI95:
    low: float
    high: float
    center: float


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("empty list")
    k = (len(sorted_values) - 1) * q
    i = int(k)
    j = min(i + 1, len(sorted_values) - 1)
    frac = k - i
    return sorted_values[i] * (1 - frac) + sorted_values[j] * frac


def ci95(values: list[float]) -> CI95:
    s = sorted(values)
    return CI95(low=percentile(s, 0.025), high=percentile(s, 0.975), center=mean(s))


def summarize_ensemble(records: list[dict]) -> dict:
    return {
        "lambda_deg": ci95([r["lambda_deg"] for r in records]).__dict__,
        "beta_deg": ci95([r["beta_deg"] for r in records]).__dict__,
        "period_hours": ci95([r["period_hours"] for r in records]).__dict__,
        "axis_a": ci95([r["axis_a"] for r in records]).__dict__,
        "axis_b": ci95([r["axis_b"] for r in records]).__dict__,
        "axis_c": ci95([r["axis_c"] for r in records]).__dict__,
    }
