from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .geometry import ellipsoid_points, rotate_z
from .photometry import brightness_from_points


def _rot_y(a: float) -> np.ndarray:
    ca, sa = np.cos(a), np.sin(a)
    return np.array([[ca, 0.0, sa], [0.0, 1.0, 0.0], [-sa, 0.0, ca]])


def _rot_z(a: float) -> np.ndarray:
    ca, sa = np.cos(a), np.sin(a)
    return np.array([[ca, -sa, 0.0], [sa, ca, 0.0], [0.0, 0.0, 1.0]])


def orientation_matrix(lon: float, lat: float) -> np.ndarray:
    return _rot_z(lon) @ _rot_y(np.pi / 2 - lat)


def model_mags(params: np.ndarray, times_h: np.ndarray, sun_dir: np.ndarray, obs_dir: np.ndarray, n_pts: int = 120) -> np.ndarray:
    a, b, c, period_h, lon, lat = params
    pts = ellipsoid_points(max(a, 0.2), max(b, 0.2), max(c, 0.2), n=n_pts)
    orient = orientation_matrix(lon, lat)
    pts = pts @ orient.T
    mags = np.zeros_like(times_h)
    for i, t in enumerate(times_h):
        theta = 2.0 * np.pi * (t / max(period_h, 0.1))
        rot = rotate_z(pts, theta)
        bness = brightness_from_points(rot, sun_dir, obs_dir)
        mags[i] = -2.5 * np.log10(bness)
    return mags


def loss(params: np.ndarray, times_h: np.ndarray, obs_mags: np.ndarray, sun_dir: np.ndarray, obs_dir: np.ndarray) -> float:
    pred = model_mags(params, times_h, sun_dir, obs_dir)
    resid = pred - obs_mags
    reg = 1e-3 * np.sum((params[:3] - np.mean(params[:3])) ** 2)
    return float(np.mean(resid ** 2) + reg)


def finite_grad(params: np.ndarray, fn, eps: float = 1e-3) -> np.ndarray:
    g = np.zeros_like(params)
    for i in range(params.size):
        p1 = params.copy(); p1[i] += eps
        p2 = params.copy(); p2[i] -= eps
        g[i] = (fn(p1) - fn(p2)) / (2 * eps)
    return g


@dataclass
class ConvexResult:
    params: np.ndarray
    objective: float


def optimize_convex(
    init: np.ndarray,
    times_h: np.ndarray,
    obs_mags: np.ndarray,
    sun_dir: np.ndarray,
    obs_dir: np.ndarray,
    iters: int = 30,
    lr: float = 0.05,
) -> ConvexResult:
    p = init.copy().astype(float)
    best_p = p.copy()
    best_l = loss(best_p, times_h, obs_mags, sun_dir, obs_dir)

    # Deterministic coarse search for period and pole before gradient refinement.
    period_grid = np.linspace(max(2.0, p[3] * 0.9), min(30.0, p[3] * 1.1), 11)
    dlon = np.radians(np.array([-16, -8, 0, 8, 16], dtype=float))
    dlat = np.radians(np.array([-12, -6, 0, 6, 12], dtype=float))
    for per in period_grid:
        for lo in dlon:
            for la in dlat:
                cand = p.copy()
                cand[3] = per
                cand[4] = (p[4] + lo + 2 * np.pi) % (2 * np.pi)
                cand[5] = np.clip(p[5] + la, -np.pi / 2, np.pi / 2)
                cur = loss(cand, times_h, obs_mags, sun_dir, obs_dir)
                if cur < best_l:
                    best_l = cur
                    best_p = cand

    p = best_p
    for _ in range(iters):
        fn = lambda x: loss(x, times_h, obs_mags, sun_dir, obs_dir)
        g = finite_grad(p, fn)
        p -= lr * g
        p[0:3] = np.clip(p[0:3], 0.4, 2.0)
        p[3] = np.clip(p[3], 2.0, 30.0)
        p[4] = (p[4] + 2 * np.pi) % (2 * np.pi)
        p[5] = np.clip(p[5], -np.pi / 2, np.pi / 2)
    return ConvexResult(params=p, objective=loss(p, times_h, obs_mags, sun_dir, obs_dir))


def pole_error_deg(true_lon: float, true_lat: float, est_lon: float, est_lat: float) -> float:
    def sph(lon: float, lat: float) -> np.ndarray:
        return np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])

    u = sph(true_lon, true_lat)
    v = sph(est_lon, est_lat)
    dot = np.clip(float(np.dot(u, v)), -1.0, 1.0)
    return float(np.degrees(np.arccos(dot)))
