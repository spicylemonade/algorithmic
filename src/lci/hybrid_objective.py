from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HybridWeights:
    w_photo: float
    w_smooth: float
    w_concavity: float


class HybridObjective:
    """Adaptive composite loss for convex-to-nonconvex handoff."""

    @staticmethod
    def schedule(stage: int) -> HybridWeights:
        # Stage 0: prioritize stable convex fit, stage 1/2 increase concavity freedom.
        if stage <= 0:
            return HybridWeights(w_photo=1.0, w_smooth=0.35, w_concavity=0.02)
        if stage == 1:
            return HybridWeights(w_photo=1.0, w_smooth=0.2, w_concavity=0.12)
        return HybridWeights(w_photo=1.0, w_smooth=0.12, w_concavity=0.25)

    @staticmethod
    def loss(
        photometric_rms: float,
        smoothness_penalty: float,
        concavity_penalty: float,
        stage: int,
    ) -> float:
        w = HybridObjective.schedule(stage)
        return (
            w.w_photo * photometric_rms
            + w.w_smooth * smoothness_penalty
            + w.w_concavity * concavity_penalty
        )
