"""Mesh I/O helpers."""
from __future__ import annotations

from typing import List, Tuple

from .geometry import Mesh


def read_obj(path: str, max_vertices: int | None = None) -> Mesh:
    verts: List[Tuple[float, float, float]] = []
    faces: List[Tuple[int, int, int]] = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.startswith('v '):
                _, x, y, z = line.strip().split()[:4]
                verts.append((float(x), float(y), float(z)))
            elif line.startswith('f '):
                parts = line.strip().split()[1:4]
                idx = []
                for p in parts:
                    idx.append(int(p.split('/')[0]) - 1)
                faces.append((idx[0], idx[1], idx[2]))

    if max_vertices is not None and len(verts) > max_vertices:
        keep = set(range(max_vertices))
        verts = verts[:max_vertices]
        faces = [tri for tri in faces if tri[0] in keep and tri[1] in keep and tri[2] in keep]
    return Mesh(verts, faces)
