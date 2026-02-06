"""Validation metrics against ground-truth meshes."""

from __future__ import annotations

import math


def _euclid(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def hausdorff_distance(points_a, points_b):
    def directed(src, dst):
        return max(min(_euclid(p, q) for q in dst) for p in src)

    return max(directed(points_a, points_b), directed(points_b, points_a))


def normalized_hausdorff(points_a, points_b, scale_km: float):
    return hausdorff_distance(points_a, points_b) / max(scale_km, 1e-9)


def volumetric_iou(voxels_a: set[tuple[int, int, int]], voxels_b: set[tuple[int, int, int]]):
    inter = len(voxels_a & voxels_b)
    union = len(voxels_a | voxels_b)
    return inter / union if union else 0.0


def photometric_rms(observed_flux, modeled_flux):
    n = max(len(observed_flux), 1)
    return math.sqrt(sum((o - m) ** 2 for o, m in zip(observed_flux, modeled_flux)) / n)


def pole_direction_error_deg(pole_a, pole_b):
    lam1, beta1 = map(math.radians, pole_a)
    lam2, beta2 = map(math.radians, pole_b)

    v1 = (math.cos(beta1) * math.cos(lam1), math.cos(beta1) * math.sin(lam1), math.sin(beta1))
    v2 = (math.cos(beta2) * math.cos(lam2), math.cos(beta2) * math.sin(lam2), math.sin(beta2))

    dot = sum(x * y for x, y in zip(v1, v2))
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))
