"""Promotion gating based on validation fidelity thresholds."""

from __future__ import annotations


def combined_deviation_percent(norm_hausdorff: float, iou: float) -> float:
    # Combined deviation in percent, lower is better.
    return 100.0 * (0.5 * norm_hausdorff + 0.5 * (1.0 - iou))


def passes_validation(norm_hausdorff: float, iou: float) -> bool:
    return combined_deviation_percent(norm_hausdorff, iou) < 5.0
