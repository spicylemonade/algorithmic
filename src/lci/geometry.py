from __future__ import annotations

import numpy as np


def fibonacci_sphere(n: int) -> np.ndarray:
    pts = np.zeros((n, 3), dtype=float)
    golden = np.pi * (3.0 - np.sqrt(5.0))
    for i in range(n):
        y = 1 - (i / float(n - 1)) * 2
        r = np.sqrt(max(0.0, 1 - y * y))
        theta = golden * i
        pts[i] = [np.cos(theta) * r, y, np.sin(theta) * r]
    return pts


def ellipsoid_points(a: float, b: float, c: float, n: int = 2000) -> np.ndarray:
    u = fibonacci_sphere(n)
    return np.column_stack((u[:, 0] * a, u[:, 1] * b, u[:, 2] * c))


def peanut_points(a: float, b: float, c: float, neck: float = 0.35, n: int = 2500) -> np.ndarray:
    u = fibonacci_sphere(n)
    x, y, z = u[:, 0], u[:, 1], u[:, 2]
    scale = 1.0 - neck * np.exp(-((x / 0.55) ** 2))
    return np.column_stack((x * a * scale, y * b, z * c))


def rotate_z(points: np.ndarray, theta: float) -> np.ndarray:
    ct, st = np.cos(theta), np.sin(theta)
    r = np.array([[ct, -st, 0.0], [st, ct, 0.0], [0.0, 0.0, 1.0]])
    return points @ r.T


def unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / (n + 1e-12)


def approximate_volume(points: np.ndarray) -> float:
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    return float(np.prod(maxs - mins) * 0.52)
