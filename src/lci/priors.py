from __future__ import annotations

import numpy as np


def is_physically_plausible(params: np.ndarray) -> bool:
    a, b, c, period_h, lon, lat = params
    if not (0.3 <= a <= 3.0 and 0.3 <= b <= 3.0 and 0.3 <= c <= 3.0):
        return False
    if min(a, b, c) <= 0:
        return False
    # Axis ratio limit to avoid extreme non-physical bodies in this model.
    axis_ratio = max(a, b, c) / min(a, b, c)
    if axis_ratio > 4.5:
        return False
    # Rotation period floor to avoid unrealistically fast spin in rubble-pile regime.
    if period_h < 2.0:
        return False
    if not (0.0 <= lon <= 2 * np.pi):
        return False
    if not (-np.pi / 2 <= lat <= np.pi / 2):
        return False
    return True
