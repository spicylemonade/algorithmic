from __future__ import annotations

import math
from dataclasses import dataclass

from .types import InversionResult, Mesh, SpinState


@dataclass
class ValidationModule:
    def hausdorff_normalized(self, predicted: Mesh, truth: Mesh) -> float:
        """Symmetric Hausdorff distance normalized by truth diameter."""
        pv = predicted.vertices
        tv = truth.vertices
        if not pv or not tv:
            return float("inf")
        max_min_p2t = 0.0
        for p in pv:
            dmin = min(math.dist(p, t) for t in tv)
            max_min_p2t = max(max_min_p2t, dmin)
        max_min_t2p = 0.0
        for t in tv:
            dmin = min(math.dist(t, p) for p in pv)
            max_min_t2p = max(max_min_t2p, dmin)
        haus = max(max_min_p2t, max_min_t2p)
        sample_step = max(1, len(tv) // 20)
        diam = max(
            math.dist(tv[i], tv[j])
            for i in range(0, len(tv), sample_step)
            for j in range(0, len(tv), sample_step)
        )
        return haus / max(diam, 1e-6)

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

    def pass_fail(self, metrics: dict[str, float]) -> bool:
        return (
            metrics["hausdorff_norm"] <= 0.05
            and (1.0 - metrics["volumetric_iou"]) <= 0.05
            and metrics["spin_axis_error_deg"] <= 10.0
            and metrics["period_error_h"] <= 0.01
        )

    def evaluate(self, pred: InversionResult, truth: InversionResult) -> dict[str, float]:
        out = {
            "hausdorff_norm": self.hausdorff_normalized(pred.mesh, truth.mesh),
            "volumetric_iou": self.volumetric_iou_proxy(pred.mesh, truth.mesh),
            "spin_axis_error_deg": self.spin_axis_error_deg(pred.spin, truth.spin),
            "period_error_h": self.period_error_hours(pred.spin, truth.spin),
        }
        out["pass"] = 1.0 if self.pass_fail(out) else 0.0
        return out
