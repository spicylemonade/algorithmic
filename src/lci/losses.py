from dataclasses import dataclass
from typing import Dict


@dataclass
class LossWeights:
    w_photo: float = 1.0
    w_smooth: float = 0.3
    w_physical: float = 0.2
    w_concavity: float = 0.4


def total_loss(components: Dict[str, float], w: LossWeights) -> float:
    return (
        w.w_photo * components.get("photo", 0.0)
        + w.w_smooth * components.get("smooth", 0.0)
        + w.w_physical * components.get("physical", 0.0)
        + w.w_concavity * components.get("concavity", 0.0)
    )


def adapt_weights(weights: LossWeights, val_error: float) -> LossWeights:
    # Validation error bands: >0.08 high, 0.04-0.08 medium, <0.04 low.
    w = LossWeights(**weights.__dict__)
    if val_error > 0.08:
        w.w_photo *= 1.2
        w.w_smooth *= 0.9
        w.w_concavity *= 1.15
    elif val_error > 0.04:
        w.w_photo *= 1.05
        w.w_physical *= 1.1
    else:
        w.w_smooth *= 1.1
        w.w_physical *= 1.1
        w.w_concavity *= 0.95
    s = w.w_photo + w.w_smooth + w.w_physical + w.w_concavity
    w.w_photo /= s
    w.w_smooth /= s
    w.w_physical /= s
    w.w_concavity /= s
    return w
