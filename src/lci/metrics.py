from __future__ import annotations

import numpy as np


def chi_square(obs: np.ndarray, pred: np.ndarray, sigma: float = 0.03) -> float:
    return float(np.mean(((obs - pred) / max(sigma, 1e-12)) ** 2))


def period_error_pct(true_p: float, est_p: float) -> float:
    return float(abs(est_p - true_p) / max(true_p, 1e-12) * 100.0)


def pole_error_deg(true_lon: float, true_lat: float, est_lon: float, est_lat: float) -> float:
    u = np.array([np.cos(true_lat) * np.cos(true_lon), np.cos(true_lat) * np.sin(true_lon), np.sin(true_lat)])
    v = np.array([np.cos(est_lat) * np.cos(est_lon), np.cos(est_lat) * np.sin(est_lon), np.sin(est_lat)])
    return float(np.degrees(np.arccos(np.clip(np.dot(u, v), -1.0, 1.0))))


def hausdorff_distance(a: np.ndarray, b: np.ndarray) -> float:
    da = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2))
    h_ab = da.min(axis=1).max()
    h_ba = da.min(axis=0).max()
    return float(max(h_ab, h_ba))


def volumetric_iou(a: np.ndarray, b: np.ndarray, voxels: int = 32) -> float:
    mins = np.minimum(a.min(axis=0), b.min(axis=0))
    maxs = np.maximum(a.max(axis=0), b.max(axis=0))
    span = maxs - mins + 1e-12

    def occ(pts: np.ndarray) -> np.ndarray:
        idx = np.floor((pts - mins) / span * (voxels - 1)).astype(int)
        idx = np.clip(idx, 0, voxels - 1)
        grid = np.zeros((voxels, voxels, voxels), dtype=bool)
        grid[idx[:, 0], idx[:, 1], idx[:, 2]] = True
        return grid

    oa = occ(a)
    ob = occ(b)
    inter = np.logical_and(oa, ob).sum()
    union = np.logical_or(oa, ob).sum()
    return float(inter / max(union, 1))


def structured_report(
    obs_mag: np.ndarray,
    pred_mag: np.ndarray,
    true_period: float,
    est_period: float,
    true_pole: tuple[float, float],
    est_pole: tuple[float, float],
    true_points: np.ndarray,
    est_points: np.ndarray,
) -> dict:
    return {
        "chi_square": chi_square(obs_mag, pred_mag),
        "period_error_pct": period_error_pct(true_period, est_period),
        "pole_error_deg": pole_error_deg(true_pole[0], true_pole[1], est_pole[0], est_pole[1]),
        "hausdorff_distance": hausdorff_distance(true_points, est_points),
        "volumetric_iou": volumetric_iou(true_points, est_points),
    }
