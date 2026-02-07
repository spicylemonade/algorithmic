from __future__ import annotations

import numpy as np

from .geometry import rotate_z, unit


def brightness_from_points(points: np.ndarray, sun_dir: np.ndarray, obs_dir: np.ndarray) -> float:
    s = unit(sun_dir)
    o = unit(obs_dir)
    normals = points / (np.linalg.norm(points, axis=1, keepdims=True) + 1e-12)
    inc = normals @ s
    emi = normals @ o
    vis = (inc > 0) & (emi > 0)
    if not np.any(vis):
        return 1e-9
    signal = np.sum(inc[vis] * emi[vis]) / points.shape[0]
    return float(max(signal, 1e-9))


def light_curve(points: np.ndarray, period_h: float, times_h: np.ndarray, sun_dir: np.ndarray, obs_dir: np.ndarray) -> np.ndarray:
    mags = np.zeros_like(times_h, dtype=float)
    for i, t in enumerate(times_h):
        theta = 2.0 * np.pi * (t / period_h)
        rot = rotate_z(points, theta)
        b = brightness_from_points(rot, sun_dir, obs_dir)
        mags[i] = -2.5 * np.log10(b)
    return mags
