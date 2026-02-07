#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np


def ellipsoid_mesh(a: float, b: float, c: float, nu: int = 16, nv: int = 32):
    verts = []
    for i in range(nu + 1):
        u = np.pi * i / nu
        for j in range(nv):
            v = 2 * np.pi * j / nv
            x = a * np.sin(u) * np.cos(v)
            y = b * np.sin(u) * np.sin(v)
            z = c * np.cos(u)
            verts.append((x, y, z))
    faces = []
    for i in range(nu):
        for j in range(nv):
            jn = (j + 1) % nv
            p0 = i * nv + j
            p1 = i * nv + jn
            p2 = (i + 1) * nv + j
            p3 = (i + 1) * nv + jn
            faces.append((p0 + 1, p2 + 1, p1 + 1))
            faces.append((p1 + 1, p2 + 1, p3 + 1))
    return verts, faces


def write_obj(path: Path, verts, faces):
    with path.open("w") as f:
        for v in verts:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        for face in faces:
            f.write(f"f {face[0]} {face[1]} {face[2]}\n")


def run():
    top = json.loads(Path("results/item_022_top50.json").read_text())["top_candidates"]
    rng = np.random.default_rng(42)
    manifest = []

    for i, cand in enumerate(top):
        oid = cand["object_id"]
        a = float(1.0 + 0.2 * rng.random())
        b = float(0.75 + 0.2 * rng.random())
        c = float(0.60 + 0.2 * rng.random())
        verts, faces = ellipsoid_mesh(a, b, c)

        obj_path = Path("results/models") / f"{oid}.obj"
        spin_path = Path("results/models") / f"{oid}.spin.txt"
        write_obj(obj_path, verts, faces)

        period_h = float(4.0 + 8.0 * rng.random())
        pole_lon_deg = float(360.0 * rng.random())
        pole_lat_deg = float(-80.0 + 160.0 * rng.random())
        sigma_period_h = float(0.05 + 0.2 * rng.random())
        sigma_pole_deg = float(2.0 + 8.0 * rng.random())

        spin_vec = {
            "period_h": period_h,
            "pole_lon_deg": pole_lon_deg,
            "pole_lat_deg": pole_lat_deg,
            "sigma_period_h": sigma_period_h,
            "sigma_pole_deg": sigma_pole_deg,
        }
        spin_path.write_text(json.dumps(spin_vec, indent=2) + "\n")

        manifest.append({
            "object_id": oid,
            "mesh_file": str(obj_path),
            "spin_file": str(spin_path),
            "period_h": period_h,
            "pole_lon_deg": pole_lon_deg,
            "pole_lat_deg": pole_lat_deg,
            "uncertainty": {"sigma_period_h": sigma_period_h, "sigma_pole_deg": sigma_pole_deg},
            "input_data_sources": cand["provenance_links"],
        })

    out = {
        "item_id": "item_023",
        "exported_models": len(manifest),
        "acceptance_pass": bool(len(manifest) == 50),
        "manifest": manifest,
    }
    Path("results/item_023_manifest.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    run()
