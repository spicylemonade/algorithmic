"""Geometry utilities for synthetic light-curve modeling and mesh handling."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

Vec3 = Tuple[float, float, float]
Face = Tuple[int, int, int]


@dataclass
class Mesh:
    vertices: List[Vec3]
    faces: List[Face]


def normalize(v: Vec3) -> Vec3:
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n == 0:
        return (0.0, 0.0, 0.0)
    return (v[0] / n, v[1] / n, v[2] / n)


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def triangle_normal_and_area(a: Vec3, b: Vec3, c: Vec3) -> Tuple[Vec3, float]:
    n = cross(sub(b, a), sub(c, a))
    area = 0.5 * math.sqrt(dot(n, n))
    return (normalize(n), area)


def rotation_matrix_z(theta: float) -> Tuple[Vec3, Vec3, Vec3]:
    c = math.cos(theta)
    s = math.sin(theta)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def mat_vec(m: Tuple[Vec3, Vec3, Vec3], v: Vec3) -> Vec3:
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


def mesh_brightness(mesh: Mesh, sun_dir: Vec3, obs_dir: Vec3, phase_coeff: float = 0.1) -> float:
    s = normalize(sun_dir)
    o = normalize(obs_dir)
    total = 0.0
    for i, j, k in mesh.faces:
        a, b, c = mesh.vertices[i], mesh.vertices[j], mesh.vertices[k]
        n, area = triangle_normal_and_area(a, b, c)
        mu0 = dot(n, s)
        mu = dot(n, o)
        if mu0 > 0.0 and mu > 0.0:
            total += area * (mu0 + phase_coeff * mu0 * mu)
    return max(total, 1e-12)


def uv_sphere(n_lat: int = 12, n_lon: int = 24, radius: float = 1.0) -> Mesh:
    verts: List[Vec3] = []
    faces: List[Face] = []
    for i in range(n_lat + 1):
        lat = -math.pi / 2 + math.pi * i / n_lat
        cl = math.cos(lat)
        sl = math.sin(lat)
        for j in range(n_lon):
            lon = 2 * math.pi * j / n_lon
            verts.append((radius * cl * math.cos(lon), radius * cl * math.sin(lon), radius * sl))

    def idx(i: int, j: int) -> int:
        return i * n_lon + (j % n_lon)

    for i in range(n_lat):
        for j in range(n_lon):
            a = idx(i, j)
            b = idx(i, j + 1)
            c = idx(i + 1, j)
            d = idx(i + 1, j + 1)
            faces.append((a, c, b))
            faces.append((b, c, d))
    return Mesh(verts, faces)


def write_obj(mesh: Mesh, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for v in mesh.vertices:
            f.write(f"v {v[0]:.8f} {v[1]:.8f} {v[2]:.8f}\n")
        for tri in mesh.faces:
            f.write(f"f {tri[0]+1} {tri[1]+1} {tri[2]+1}\n")
