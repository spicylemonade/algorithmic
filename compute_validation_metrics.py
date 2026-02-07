#!/usr/bin/env python
"""Compute error metrics between blind inversion results and ground truth shapes.

Loads the benchmark manifest, and for each target that has a recovered mesh
under ``results/blind_tests/<name>/``, computes:

  - Hausdorff distance (normalised by reference bounding-box diagonal)
  - Volumetric IoU
  - Chamfer distance
  - Spin-pole angular error (degrees)
  - Sidereal period error (hours)
  - Final chi-squared from convergence log

Results are written to ``results/validation_metrics.csv`` and a summary
table is printed to stdout.
"""

import csv
import json
import os
import sys

import numpy as np

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
# Ensure the repo root is on sys.path so local modules are importable.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from forward_model import load_obj  # noqa: E402
from mesh_comparator import compare_meshes  # noqa: E402

# ---------------------------------------------------------------------------
# Paths (all relative to REPO_ROOT/results)
# ---------------------------------------------------------------------------
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
MANIFEST_PATH = os.path.join(RESULTS_DIR, "benchmark_manifest.json")
GROUND_TRUTH_DIR = os.path.join(RESULTS_DIR, "ground_truth")
BLIND_TESTS_DIR = os.path.join(RESULTS_DIR, "blind_tests")
OUTPUT_CSV = os.path.join(RESULTS_DIR, "validation_metrics.csv")


# ---------------------------------------------------------------------------
# Helper: angular separation between two ecliptic pole directions
# ---------------------------------------------------------------------------
def angular_separation(lam1, bet1, lam2, bet2):
    """Compute the angular separation (degrees) between two directions
    given in ecliptic longitude/latitude.

    Parameters
    ----------
    lam1, bet1 : float
        Longitude and latitude of the first direction (degrees).
    lam2, bet2 : float
        Longitude and latitude of the second direction (degrees).

    Returns
    -------
    float
        Angular separation in degrees.
    """
    lam1, bet1, lam2, bet2 = [np.radians(x) for x in (lam1, bet1, lam2, bet2)]
    cos_sep = (np.sin(bet1) * np.sin(bet2)
               + np.cos(bet1) * np.cos(bet2) * np.cos(lam1 - lam2))
    return float(np.degrees(np.arccos(np.clip(cos_sep, -1.0, 1.0))))


# ---------------------------------------------------------------------------
# Helper: normalised Hausdorff (symmetric Hausdorff / bbox diagonal)
# ---------------------------------------------------------------------------
def _bounding_box_diagonal(mesh):
    """Return the Euclidean length of the bounding-box diagonal."""
    bbox_min = mesh.vertices.min(axis=0)
    bbox_max = mesh.vertices.max(axis=0)
    return float(np.linalg.norm(bbox_max - bbox_min))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # 1. Load benchmark manifest -------------------------------------------
    with open(MANIFEST_PATH, "r") as fh:
        manifest = json.load(fh)

    targets = manifest["targets"]  # dict keyed by target name

    # Prepare rows for CSV
    fieldnames = [
        "target",
        "hausdorff_norm",
        "iou",
        "chamfer",
        "pole_error_deg",
        "period_error_hr",
        "chi2_final",
    ]
    rows = []

    # 2. Iterate over targets ---------------------------------------------
    for name, info in targets.items():
        name_lower = name.lower()
        recovered_obj_path = os.path.join(
            BLIND_TESTS_DIR, name_lower, "recovered.obj"
        )

        if not os.path.isfile(recovered_obj_path):
            print(f"[SKIP] {name}: recovered.obj not found at {recovered_obj_path}")
            continue

        # 2a. Load ground truth mesh
        gt_obj_path = os.path.join(GROUND_TRUTH_DIR, f"{name_lower}.obj")
        gt_mesh = load_obj(gt_obj_path)

        # 2b. Load recovered mesh
        rec_mesh = load_obj(recovered_obj_path)

        # 2c. Load ground truth spin
        gt_spin_path = os.path.join(GROUND_TRUTH_DIR, f"{name_lower}_spin.json")
        with open(gt_spin_path, "r") as fh:
            gt_spin = json.load(fh)

        # 2d. Load recovered spin
        rec_spin_path = os.path.join(
            BLIND_TESTS_DIR, name_lower, "recovered_spin.json"
        )
        with open(rec_spin_path, "r") as fh:
            rec_spin = json.load(fh)

        # 2e. Scale recovered mesh to match GT bounding box ----------------
        gt_diag = _bounding_box_diagonal(gt_mesh)
        rec_diag = _bounding_box_diagonal(rec_mesh)
        if rec_diag > 0 and gt_diag > 0:
            scale = gt_diag / rec_diag
            from forward_model import TriMesh as _TM
            scaled_verts = rec_mesh.vertices * scale
            rec_mesh = _TM(vertices=scaled_verts, faces=rec_mesh.faces,
                           normals=rec_mesh.normals, areas=rec_mesh.areas * scale**2)

        # 2f. Compare meshes -----------------------------------------------
        metrics = compare_meshes(gt_mesh, rec_mesh, n_surface_points=10000,
                                 voxel_resolution=64)

        hausdorff_sym = metrics["hausdorff_symmetric"]
        bbox_diag = _bounding_box_diagonal(gt_mesh)
        hausdorff_norm = hausdorff_sym / bbox_diag if bbox_diag > 0 else float("nan")
        iou = metrics["iou"]
        chamfer = metrics["chamfer_distance"]

        # 2g. Pole angular error -------------------------------------------
        pole_error_deg = angular_separation(
            gt_spin["lambda_deg"], gt_spin["beta_deg"],
            rec_spin["lambda_deg"], rec_spin["beta_deg"],
        )

        # 2g. Period error -------------------------------------------------
        period_error_hr = abs(gt_spin["period_hours"] - rec_spin["period_hours"])

        # 2h. chi2_final from convergence log ------------------------------
        convergence_path = os.path.join(
            BLIND_TESTS_DIR, name_lower, "convergence.json"
        )
        chi2_final = float("nan")
        if os.path.isfile(convergence_path):
            with open(convergence_path, "r") as fh:
                convergence = json.load(fh)
            chi2_final = convergence.get("chi_squared_final",
                                        convergence.get("chi2_final", float("nan")))

        row = {
            "target": name,
            "hausdorff_norm": f"{hausdorff_norm:.6f}",
            "iou": f"{iou:.6f}",
            "chamfer": f"{chamfer:.6f}",
            "pole_error_deg": f"{pole_error_deg:.4f}",
            "period_error_hr": f"{period_error_hr:.6f}",
            "chi2_final": f"{chi2_final:.4f}" if not np.isnan(chi2_final) else "nan",
        }
        rows.append(row)

    # 3. Write CSV ---------------------------------------------------------
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")

    # 4. Print summary table -----------------------------------------------
    if not rows:
        print("\nNo targets with recovered results found.")
        return

    # Column widths
    col_widths = {fn: max(len(fn), max(len(r[fn]) for r in rows)) for fn in fieldnames}
    header = " | ".join(fn.ljust(col_widths[fn]) for fn in fieldnames)
    sep = "-+-".join("-" * col_widths[fn] for fn in fieldnames)
    print(f"\n{header}")
    print(sep)
    for row in rows:
        line = " | ".join(str(row[fn]).ljust(col_widths[fn]) for fn in fieldnames)
        print(line)
    print()


if __name__ == "__main__":
    main()
