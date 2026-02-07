from __future__ import annotations

import math
from dataclasses import dataclass

from .types import InversionResult, Mesh, SpinState


@dataclass
class ValidationModule:
    def hausdorff_normalized(self, predicted: Mesh, truth: Mesh) -> float:
        pv = predicted.vertices
        tv = truth.vertices
        if not pv or not tv:
            return float("inf")
        max_min = 0.0
        for p in pv:
            dmin = min(math.dist(p, t) for t in tv)
            max_min = max(max_min, dmin)
        diam = max(math.dist(tv[i], tv[j]) for i in range(0, len(tv), max(1, len(tv)//20)) for j in range(0, len(tv), max(1, len(tv)//20)))
        return max_min / max(diam, 1e-6)

    def volumetric_iou_proxy(self, predicted: Mesh, truth: Mesh) -> float:
        n1 = len(predicted.vertices)
        n2 = len(truth.vertices)
        inter = min(n1, n2)
        union = max(n1, n2)
        return inter / union if union else 0.0

    def spin_axis_error_deg(self, pred: SpinState, truth: SpinState) -> float:
        return abs(pred.beta_deg - truth.beta_deg)

    def period_error_hours(self, pred: SpinState, truth: SpinState) -> float:
        return abs(pred.period_hours - truth.period_hours)

    def evaluate(self, pred: InversionResult, truth: InversionResult) -> dict[str, float]:
        return {
            "hausdorff_norm": self.hausdorff_normalized(pred.mesh, truth.mesh),
            "volumetric_iou": self.volumetric_iou_proxy(pred.mesh, truth.mesh),
            "spin_axis_error_deg": self.spin_axis_error_deg(pred.spin, truth.spin),
            "period_error_h": self.period_error_hours(pred.spin, truth.spin),
        }
