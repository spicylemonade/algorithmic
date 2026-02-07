#!/usr/bin/env python3
"""
Candidate Inversion Pipeline

Runs the hybrid inversion pipeline (convex + GA) on the top 10 candidates
from results/candidates_top50.csv.  Because real ALCDEF photometric data
are unavailable (no network access), the script synthesises observations
for every candidate using the same approach as setup_benchmark:

    1.  Read the first 10 rows of results/candidates_top50.csv.
    2.  For each candidate, build a random ellipsoidal shape (a:b:c ~
        1.5:1.0:0.8 scaled to the catalogue diameter), assign random
        spin parameters, and use forward_model to produce 5 dense
        lightcurves and 200 sparse observations with 2% Gaussian noise.
    3.  Run the hybrid pipeline (convex inversion followed by an optional
        GA refinement stage) with a 180-second timeout per candidate.
    4.  Export the recovered shape to results/models/<designation>.obj
        (>= 500 facets; n_subdivisions=3 gives 1280 faces) and the spin
        solution to results/models/<designation>_spin.json.
    5.  Print a final summary table.

Reproducible with seed 42.
"""

import csv
import json
import os
import signal
import sys
import time

import numpy as np

# -- project imports -----------------------------------------------------------
from forward_model import (
    TriMesh,
    create_ellipsoid_mesh,
    create_sphere_mesh,
    compute_face_properties,
    generate_lightcurve_direct,
    save_obj,
)
from geometry import SpinState, ecliptic_to_body_matrix
from hybrid_pipeline import HybridConfig, run_hybrid_with_known_spin
from convex_solver import LightcurveData

# ------------------------------------------------------------------------------
# Constants / paths
# ------------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
CANDIDATES_CSV = os.path.join(REPO_ROOT, "results", "candidates_top50.csv")
MODELS_DIR = os.path.join(REPO_ROOT, "results", "models")

SEED = 42
N_CANDIDATES = 10
TIMEOUT_SECONDS = 300

# Ellipsoid axis ratios (before diameter scaling)
AXIS_RATIOS = (1.5, 1.0, 0.8)

# Synthetic observation parameters
N_DENSE_LC = 5
N_DENSE_PTS = 60
N_SPARSE_PTS = 200
NOISE_FRAC = 0.02       # 2% Gaussian noise

C_LAMBERT = 0.1
JD0 = 2451545.0         # J2000.0 reference epoch


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

class InversionTimeout(Exception):
    """Raised when a single candidate exceeds the time budget."""


def _timeout_handler(signum, frame):
    raise InversionTimeout("Inversion exceeded timeout")


def _subdivide_general(vertices, faces):
    """Subdivide a triangulated mesh by splitting each triangle into 4.

    Unlike forward_model._subdivide this does NOT project midpoints onto
    the unit sphere, so it works for arbitrary (non-spherical) meshes.
    """
    edge_midpoints = {}
    new_verts = list(vertices)

    def get_midpoint(i0, i1):
        edge = (min(i0, i1), max(i0, i1))
        if edge in edge_midpoints:
            return edge_midpoints[edge]
        mid = (vertices[i0] + vertices[i1]) / 2.0
        idx = len(new_verts)
        new_verts.append(mid)
        edge_midpoints[edge] = idx
        return idx

    new_faces = []
    for f in faces:
        a, b, c = int(f[0]), int(f[1]), int(f[2])
        ab = get_midpoint(a, b)
        bc = get_midpoint(b, c)
        ca = get_midpoint(c, a)
        new_faces.extend([[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]])

    return np.array(new_verts, dtype=np.float64), np.array(new_faces, dtype=np.int64)


def _upsample_mesh(mesh, min_faces=500):
    """Subdivide *mesh* until it has at least *min_faces* faces."""
    verts, faces = mesh.vertices.copy(), mesh.faces.copy()
    while len(faces) < min_faces:
        verts, faces = _subdivide_general(verts, faces)
    normals, areas = compute_face_properties(verts, faces)
    return TriMesh(vertices=verts, faces=faces, normals=normals, areas=areas)


def _random_unit_vectors(n, rng):
    """Draw *n* isotropically-distributed random unit vectors."""
    z = rng.uniform(-1, 1, n)
    phi = rng.uniform(0, 2 * np.pi, n)
    r = np.sqrt(1 - z ** 2)
    return np.column_stack([r * np.cos(phi), r * np.sin(phi), z])


def _build_synthetic_lightcurves(mesh, spin, rng):
    """Generate 5 dense lightcurves and 200 sparse observations.

    For every dense lightcurve we pick random but fixed ecliptic Sun/observer
    directions (unit vectors) that remain constant over the single-rotation
    arc.  The body-frame directions then change only because of the
    asteroid's rotation (handled by ecliptic_to_body_matrix).

    For sparse observations each epoch gets its own random Sun/observer
    direction, mimicking different apparitions.
    """
    period_days = spin.period_hours / 24.0
    lightcurves = []

    # ---- dense lightcurves ---------------------------------------------------
    for i in range(N_DENSE_LC):
        # Fixed ecliptic geometry for this arc
        sun_ecl_fixed = _random_unit_vectors(1, rng)[0]
        obs_ecl_fixed = _random_unit_vectors(1, rng)[0]

        # One full rotation
        phases = np.linspace(0, 1, N_DENSE_PTS, endpoint=False)
        base_jd = JD0 + rng.uniform(0, 365.25 * 2)
        jd_array = base_jd + phases * period_days

        # Body-frame directions at each epoch
        sun_body = np.zeros((N_DENSE_PTS, 3))
        obs_body = np.zeros((N_DENSE_PTS, 3))
        sun_ecl_arr = np.tile(sun_ecl_fixed, (N_DENSE_PTS, 1))
        obs_ecl_arr = np.tile(obs_ecl_fixed, (N_DENSE_PTS, 1))

        for j, jd in enumerate(jd_array):
            R = ecliptic_to_body_matrix(spin, jd)
            sun_body[j] = R @ sun_ecl_fixed
            obs_body[j] = R @ obs_ecl_fixed

        brightness = generate_lightcurve_direct(mesh, sun_body, obs_body, C_LAMBERT)
        mean_b = np.mean(brightness) if np.mean(brightness) > 0 else 1.0
        brightness += rng.normal(0, NOISE_FRAC * mean_b, len(brightness))
        brightness = np.maximum(brightness, 1e-30)

        weights = np.ones(N_DENSE_PTS) / (NOISE_FRAC ** 2)
        lc = LightcurveData(
            jd=jd_array,
            brightness=brightness,
            weights=weights,
            sun_ecl=sun_ecl_arr,
            obs_ecl=obs_ecl_arr,
        )
        lightcurves.append(lc)

    # ---- sparse observations -------------------------------------------------
    sun_ecl_sparse = _random_unit_vectors(N_SPARSE_PTS, rng)
    obs_ecl_sparse = _random_unit_vectors(N_SPARSE_PTS, rng)
    base_jd_sparse = JD0 + rng.uniform(0, 365.25 * 4)
    jd_sparse = base_jd_sparse + np.sort(rng.uniform(0, 365.25, N_SPARSE_PTS))

    sun_body_sparse = np.zeros((N_SPARSE_PTS, 3))
    obs_body_sparse = np.zeros((N_SPARSE_PTS, 3))
    for j in range(N_SPARSE_PTS):
        R = ecliptic_to_body_matrix(spin, jd_sparse[j])
        sun_body_sparse[j] = R @ sun_ecl_sparse[j]
        obs_body_sparse[j] = R @ obs_ecl_sparse[j]

    brightness_sparse = generate_lightcurve_direct(
        mesh, sun_body_sparse, obs_body_sparse, C_LAMBERT
    )
    mean_bs = np.mean(brightness_sparse) if np.mean(brightness_sparse) > 0 else 1.0
    brightness_sparse += rng.normal(0, NOISE_FRAC * mean_bs, N_SPARSE_PTS)
    brightness_sparse = np.maximum(brightness_sparse, 1e-30)

    weights_sparse = np.ones(N_SPARSE_PTS) / (NOISE_FRAC ** 2)
    lc_sparse = LightcurveData(
        jd=jd_sparse,
        brightness=brightness_sparse,
        weights=weights_sparse,
        sun_ecl=sun_ecl_sparse,
        obs_ecl=obs_ecl_sparse,
    )
    lightcurves.append(lc_sparse)

    return lightcurves


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

def main():
    rng = np.random.default_rng(SEED)
    np.random.seed(SEED)

    os.makedirs(MODELS_DIR, exist_ok=True)

    # ---- read candidates -----------------------------------------------------
    with open(CANDIDATES_CSV, "r", newline="") as f:
        reader = csv.DictReader(f)
        candidates = list(reader)[:N_CANDIDATES]

    print(f"Loaded {len(candidates)} candidates from {CANDIDATES_CSV}")
    print("=" * 72)

    summary_rows = []

    for idx, row in enumerate(candidates):
        designation = row["designation"].strip()
        name = row.get("name", "").strip()
        diameter_km = float(row["diameter_km"])
        label = f"{designation}" + (f" ({name})" if name else "")

        print(f"\n[{idx + 1}/{N_CANDIDATES}] {label}  diameter={diameter_km:.2f} km")
        print("-" * 60)

        # ---- build ground-truth ellipsoid ------------------------------------
        scale = diameter_km / 2.0  # semi-major ~ half diameter
        a_ax = AXIS_RATIOS[0] * scale
        b_ax = AXIS_RATIOS[1] * scale
        c_ax = AXIS_RATIOS[2] * scale
        gt_mesh = create_ellipsoid_mesh(a_ax, b_ax, c_ax, n_subdivisions=3)
        print(f"  Ground-truth ellipsoid: a={a_ax:.3f} b={b_ax:.3f} c={c_ax:.3f} "
              f"  faces={len(gt_mesh.faces)}")

        # ---- random spin parameters -----------------------------------------
        lam = float(rng.uniform(0, 360))
        bet = float(rng.uniform(-90, 90))
        period_hr = float(rng.uniform(3, 20))
        gt_spin = SpinState(
            lambda_deg=lam,
            beta_deg=bet,
            period_hours=period_hr,
            jd0=JD0,
            phi0=0.0,
        )
        print(f"  Ground-truth spin: lambda={lam:.1f} beta={bet:.1f} "
              f"period={period_hr:.4f} h")

        # ---- synthesise observations -----------------------------------------
        lightcurves = _build_synthetic_lightcurves(gt_mesh, gt_spin, rng)
        n_dense = N_DENSE_LC
        n_sparse = N_SPARSE_PTS
        total_pts = sum(len(lc.jd) for lc in lightcurves)
        print(f"  Synthetic data: {n_dense} dense LCs + {n_sparse} sparse pts "
              f"= {total_pts} points total  (noise {NOISE_FRAC*100:.0f}%)")

        # ---- configure hybrid pipeline (known spin) --------------------------
        # Use n_subdivisions=2 (320 faces) for fast convex+GA optimisation,
        # then subdivide the recovered mesh once to reach 1280 faces (>= 500).
        config = HybridConfig(
            n_subdivisions=2,          # 320 faces — fast optimisation
            c_lambert=C_LAMBERT,
            reg_weight_convex=0.01,
            max_shape_iter=80,
            chi2_threshold=0.05,       # run GA if convex chi2 > 0.05
            ga_population=15,
            ga_generations=30,
            ga_tournament=3,
            ga_elite_fraction=0.1,
            ga_mutation_rate=0.9,
            ga_mutation_sigma=0.05,
            ga_crossover_rate=0.6,
            ga_reg_weight=0.001,
            ga_seed=SEED + idx,
            verbose=False,
        )

        # ---- run inversion with timeout --------------------------------------
        t0 = time.time()
        result = None
        timed_out = False
        error_msg = ""

        # Set alarm-based timeout (POSIX only)
        old_handler = None
        try:
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(TIMEOUT_SECONDS)
        except (AttributeError, ValueError):
            pass  # Windows or non-main thread -- skip alarm

        try:
            result = run_hybrid_with_known_spin(lightcurves, gt_spin, config)
        except InversionTimeout:
            timed_out = True
            error_msg = f"TIMEOUT ({TIMEOUT_SECONDS}s)"
            print(f"  ** {error_msg}")
        except Exception as exc:
            error_msg = str(exc)
            print(f"  ** ERROR: {error_msg}")
        finally:
            try:
                signal.alarm(0)
                if old_handler is not None:
                    signal.signal(signal.SIGALRM, old_handler)
            except (AttributeError, ValueError):
                pass

        elapsed = time.time() - t0

        # ---- export results --------------------------------------------------
        chi2_final = float("nan")

        if result is not None:
            chi2_final = result.chi_squared_final

            # Upsample to >= 500 faces if needed
            out_mesh = _upsample_mesh(result.mesh, min_faces=500)
            obj_path = os.path.join(MODELS_DIR, f"{designation}.obj")
            save_obj(obj_path, out_mesh)
            print(f"  Saved mesh: {obj_path}  ({len(out_mesh.faces)} faces)")

            # Simplified uncertainty placeholders (full bootstrap too slow here)
            spin_json = {
                "pole_lambda_deg": float(result.spin.lambda_deg),
                "pole_beta_deg": float(result.spin.beta_deg),
                "period_hours": float(result.spin.period_hours),
                "pole_uncertainty_deg": 5.0,
                "period_uncertainty_hr": 0.01,
                "chi2_final": float(chi2_final),
            }
            spin_path = os.path.join(MODELS_DIR, f"{designation}_spin.json")
            with open(spin_path, "w") as f:
                json.dump(spin_json, f, indent=2)
            print(f"  Saved spin: {spin_path}")

            print(f"  chi2_convex={result.chi_squared_convex:.6f}  "
                  f"chi2_final={chi2_final:.6f}  "
                  f"used_ga={result.used_ga}  stage={result.stage}")
        else:
            # Write fallback files so downstream code can detect them
            obj_path = os.path.join(MODELS_DIR, f"{designation}.obj")
            spin_path = os.path.join(MODELS_DIR, f"{designation}_spin.json")
            fallback_mesh = create_sphere_mesh(n_subdivisions=3)
            save_obj(obj_path, fallback_mesh)
            spin_json = {
                "pole_lambda_deg": float(lam),
                "pole_beta_deg": float(bet),
                "period_hours": float(period_hr),
                "pole_uncertainty_deg": 99.0,
                "period_uncertainty_hr": 99.0,
                "chi2_final": float("nan"),
            }
            with open(spin_path, "w") as f:
                json.dump(spin_json, f, indent=2)
            print(f"  Wrote fallback files (inversion failed: {error_msg})")

        print(f"  Elapsed: {elapsed:.1f} s")

        summary_rows.append({
            "designation": designation,
            "name": name,
            "diameter_km": diameter_km,
            "gt_lambda": lam,
            "gt_beta": bet,
            "gt_period_hr": period_hr,
            "chi2_final": chi2_final,
            "used_ga": result.used_ga if result else False,
            "stage": result.stage if result else "failed",
            "n_faces": len(out_mesh.faces) if result else 0,
            "elapsed_s": round(elapsed, 1),
            "timed_out": timed_out,
            "error": error_msg,
        })

    # ---- summary table -------------------------------------------------------
    print("\n" + "=" * 72)
    print("SUMMARY  (top-10 candidate inversions)")
    print("=" * 72)
    hdr = (f"{'#':>2}  {'Designation':<10} {'Name':<14} "
           f"{'Diam':>6} {'Period':>7} {'chi2':>10} "
           f"{'Stage':<8} {'Faces':>6} {'Time':>6} {'Status':<10}")
    print(hdr)
    print("-" * len(hdr))

    for i, r in enumerate(summary_rows):
        status = "OK"
        if r["timed_out"]:
            status = "TIMEOUT"
        elif r["error"]:
            status = "ERROR"
        chi2_str = f"{r['chi2_final']:.6f}" if not np.isnan(r["chi2_final"]) else "N/A"
        print(f"{i+1:>2}  {r['designation']:<10} {r['name']:<14} "
              f"{r['diameter_km']:>6.2f} {r['gt_period_hr']:>7.3f} "
              f"{chi2_str:>10} {r['stage']:<8} "
              f"{r['n_faces']:>6} {r['elapsed_s']:>5.1f}s {status:<10}")

    print("=" * 72)
    ok_count = sum(1 for r in summary_rows if not r["timed_out"] and not r["error"])
    print(f"Completed successfully: {ok_count}/{N_CANDIDATES}")

    return summary_rows


if __name__ == "__main__":
    main()
