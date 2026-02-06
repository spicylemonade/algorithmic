"""Validation metrics and confidence scoring."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from .geometry import Mesh

Vec3 = Tuple[float, float, float]


@dataclass
class MetricBundle:
    normalized_hausdorff: float
    volumetric_iou: float
    lightcurve_rmse: float
    pole_angle_error_deg: float
    confidence: float


def _dist(a: Vec3, b: Vec3) -> float:
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)


def hausdorff_distance(a_pts: Sequence[Vec3], b_pts: Sequence[Vec3]) -> float:
    def directed(x: Sequence[Vec3], y: Sequence[Vec3]) -> float:
        m = 0.0
        for p in x:
            d = min(_dist(p, q) for q in y)
            m = max(m, d)
        return m
    return max(directed(a_pts, b_pts), directed(b_pts, a_pts))


def normalized_hausdorff(mesh_a: Mesh, mesh_b: Mesh) -> float:
    h = hausdorff_distance(mesh_a.vertices, mesh_b.vertices)
    scale = max(1e-9, max(math.sqrt(v[0]**2+v[1]**2+v[2]**2) for v in mesh_b.vertices))
    return h / scale


def bbox_iou(mesh_a: Mesh, mesh_b: Mesh) -> float:
    def box(mesh: Mesh):
        xs = [v[0] for v in mesh.vertices]
        ys = [v[1] for v in mesh.vertices]
        zs = [v[2] for v in mesh.vertices]
        return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    ax0, ax1, ay0, ay1, az0, az1 = box(mesh_a)
    bx0, bx1, by0, by1, bz0, bz1 = box(mesh_b)
    ix = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    iy = max(0.0, min(ay1, by1) - max(ay0, by0))
    iz = max(0.0, min(az1, bz1) - max(az0, bz0))
    inter = ix * iy * iz
    va = max(0.0, (ax1 - ax0) * (ay1 - ay0) * (az1 - az0))
    vb = max(0.0, (bx1 - bx0) * (by1 - by0) * (bz1 - bz0))
    union = va + vb - inter
    return inter / union if union > 0 else 0.0


def lightcurve_rmse(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    n = min(len(y_true), len(y_pred))
    if n == 0:
        return float("inf")
    return math.sqrt(sum((y_true[i] - y_pred[i]) ** 2 for i in range(n)) / n)


def pole_angle_error_deg(true_lambda: float, true_beta: float, pred_lambda: float, pred_beta: float) -> float:
    tl = math.radians(true_lambda)
    tb = math.radians(true_beta)
    pl = math.radians(pred_lambda)
    pb = math.radians(pred_beta)
    t = (math.cos(tb) * math.cos(tl), math.cos(tb) * math.sin(tl), math.sin(tb))
    p = (math.cos(pb) * math.cos(pl), math.cos(pb) * math.sin(pl), math.sin(pb))
    c = max(-1.0, min(1.0, t[0]*p[0] + t[1]*p[1] + t[2]*p[2]))
    return math.degrees(math.acos(c))


def calibrated_confidence(norm_hd: float, iou: float, rmse: float, pole_err_deg: float) -> float:
    # Monotonic score components calibrated to 0-1 domain.
    s_hd = max(0.0, min(1.0, 1.0 - norm_hd / 0.05))
    s_iou = max(0.0, min(1.0, iou))
    s_rmse = max(0.0, min(1.0, 1.0 - rmse / 0.1))
    s_pole = max(0.0, min(1.0, 1.0 - pole_err_deg / 30.0))
    return 0.35 * s_hd + 0.25 * s_iou + 0.2 * s_rmse + 0.2 * s_pole


def evaluate(true_mesh: Mesh, pred_mesh: Mesh, y_true: Sequence[float], y_pred: Sequence[float], true_pole: Tuple[float, float], pred_pole: Tuple[float, float]) -> MetricBundle:
    n_hd = normalized_hausdorff(pred_mesh, true_mesh)
    iou = bbox_iou(pred_mesh, true_mesh)
    rmse = lightcurve_rmse(y_true, y_pred)
    pa = pole_angle_error_deg(true_pole[0], true_pole[1], pred_pole[0], pred_pole[1])
    conf = calibrated_confidence(n_hd, iou, rmse, pa)
    return MetricBundle(n_hd, iou, rmse, pa, conf)


def confidence_thresholds() -> dict:
    return {
        "high_confidence_min": 0.8,
        "medium_confidence_min": 0.6,
        "low_confidence_min": 0.4,
        "pass_deviation_max": 0.05,
    }
