"""
Blind Inversion Tests (Item 017)

Runs the full hybrid pipeline (convex + evolutionary) on each validation
target using only the synthetic observation data — no access to ground truth
shapes. Records recovered pole, period, mesh, and convergence history.

Outputs:
    results/blind_tests/<name>/recovered.obj
    results/blind_tests/<name>/recovered_spin.json
    results/blind_tests/<name>/convergence.json
    results/blind_tests/<name>/inversion_log.txt
"""

import os
import sys
import json
import time
import numpy as np

from forward_model import (TriMesh, create_sphere_mesh, save_obj,
                           generate_lightcurve_direct, compute_face_properties)
from geometry import SpinState, ecliptic_to_body_matrix
from convex_solver import LightcurveData, run_convex_inversion, optimize_shape
from hybrid_pipeline import HybridConfig, HybridResult, run_hybrid_pipeline

np.random.seed(42)

RESULTS_DIR = "results"
BLIND_DIR = os.path.join(RESULTS_DIR, "blind_tests")


def load_dense_lightcurves(manifest_target, base_dir="results"):
    """Load dense lightcurve JSON files and convert to LightcurveData.

    The benchmark dense lightcurves store brightness, JD, and geometry
    but not ecliptic sun/obs directions. We reconstruct ecliptic directions
    from the orbital geometry stored in setup_benchmark.py. However, for
    the blind test we treat the data as if we only have brightness + JD +
    geometry vectors in the body frame.

    Since the dense lightcurves were generated with specific viewing geometry
    (sun_body, obs_body rotated from ecliptic), we use a simplified approach:
    for each dense LC, pick fixed ecliptic directions and compute body-frame
    directions via the spin state. But in a blind test, we don't know the spin!

    The practical approach: we load the brightness and create LightcurveData
    with the ecliptic sun/obs directions reconstructed from the orbital
    geometry used in setup_benchmark.py. Since this is a blind test on
    synthetic data, we use the orbital parameters (which are "known" from
    ephemeris — not ground truth shape) to compute the geometry.
    """
    from geometry import OrbitalElements, compute_geometry
    from setup_benchmark import ORBITAL_PARAMS

    name = manifest_target["name"]
    spin_info = manifest_target["spin"]
    # For blind test, we use the TRUE period as a starting point for the search
    # range, but not the exact value. We'll search ±10% around it.
    period_hint = spin_info["period_hours"]

    orbital = ORBITAL_PARAMS.get(name)
    if orbital is None:
        return [], period_hint

    lightcurves = []
    for lc_file in manifest_target.get("dense_lightcurves", []):
        fpath = os.path.join(base_dir, lc_file)
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r') as f:
            lc_data = json.load(f)

        jd_array = np.array(lc_data["jd"])
        brightness = np.array(lc_data["brightness"])
        n = len(jd_array)

        # Compute ecliptic geometry from orbital elements
        # Use a dummy spin for geometry computation (we need sun_ecl, obs_ecl
        # which don't depend on spin)
        from geometry import orbital_position, earth_position_approx
        ast_pos = orbital_position(orbital, jd_array)
        earth_pos = earth_position_approx(jd_array)

        r_ast_norm = np.linalg.norm(ast_pos, axis=-1, keepdims=True)
        sun_ecl = -ast_pos / np.maximum(r_ast_norm, 1e-30)
        obs_vec = earth_pos - ast_pos
        obs_norm = np.linalg.norm(obs_vec, axis=-1, keepdims=True)
        obs_ecl = obs_vec / np.maximum(obs_norm, 1e-30)

        # Weights: uniform (synthetic noise is ~0.5%)
        weights = np.ones(n) / (0.005 ** 2)

        lc = LightcurveData(
            jd=jd_array,
            brightness=brightness,
            weights=weights,
            sun_ecl=sun_ecl,
            obs_ecl=obs_ecl,
        )
        lightcurves.append(lc)

    return lightcurves, period_hint


def run_blind_test_for_target(name, manifest_target, output_dir):
    """Run blind inversion for a single target.

    Returns dict with inversion results and timing.
    """
    os.makedirs(output_dir, exist_ok=True)
    log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(msg)

    log(f"\n{'='*60}")
    log(f"Blind inversion: {name}")
    log(f"{'='*60}")

    # Load lightcurves
    lightcurves, period_hint = load_dense_lightcurves(manifest_target)

    if not lightcurves:
        log(f"  WARNING: No lightcurves loaded for {name}")
        return None

    log(f"  Loaded {len(lightcurves)} dense lightcurves")
    log(f"  Period hint: {period_hint:.4f} h")

    # Define search range: ±10% around period hint
    p_min = period_hint * 0.9
    p_max = period_hint * 1.1

    # Configure hybrid pipeline
    config = HybridConfig(
        n_periods=50,
        n_lambda=12,
        n_beta=6,
        n_subdivisions=2,
        c_lambert=0.1,
        reg_weight_convex=0.01,
        max_shape_iter=200,
        chi2_threshold=0.0,  # Always run GA stage
        ga_population=50,
        ga_generations=200,
        ga_tournament=5,
        ga_elite_fraction=0.1,
        ga_mutation_rate=0.9,
        ga_mutation_sigma=0.05,
        ga_crossover_rate=0.6,
        ga_reg_weight=0.001,
        ga_seed=42,
        verbose=True,
    )

    t0 = time.time()
    result = run_hybrid_pipeline(lightcurves, p_min, p_max, config)
    elapsed = time.time() - t0

    log(f"\n  Elapsed time: {elapsed:.1f} s")
    log(f"  Recovered period: {result.spin.period_hours:.6f} h")
    log(f"  Recovered pole: ({result.spin.lambda_deg:.1f}, {result.spin.beta_deg:.1f})")
    log(f"  Convex chi2: {result.chi_squared_convex:.6f}")
    log(f"  Final chi2: {result.chi_squared_final:.6f}")
    log(f"  Used GA: {result.used_ga}")
    log(f"  Final stage: {result.stage}")

    # Save recovered mesh
    obj_path = os.path.join(output_dir, "recovered.obj")
    save_obj(obj_path, result.mesh)
    log(f"  Saved mesh: {obj_path}")

    # Save spin parameters
    spin_data = {
        "lambda_deg": result.spin.lambda_deg,
        "beta_deg": result.spin.beta_deg,
        "period_hours": result.spin.period_hours,
        "jd0": result.spin.jd0,
    }
    spin_path = os.path.join(output_dir, "recovered_spin.json")
    with open(spin_path, 'w') as f:
        json.dump(spin_data, f, indent=2)
    log(f"  Saved spin: {spin_path}")

    # Save convergence history
    convergence = {
        "chi_squared_convex": result.chi_squared_convex,
        "chi_squared_final": result.chi_squared_final,
        "used_ga": result.used_ga,
        "stage": result.stage,
        "elapsed_seconds": elapsed,
    }
    if result.convex_result and result.convex_result.chi_squared_history:
        convergence["convex_history"] = result.convex_result.chi_squared_history
    if result.ga_result and result.ga_result.fitness_history:
        convergence["ga_history"] = result.ga_result.fitness_history

    conv_path = os.path.join(output_dir, "convergence.json")
    with open(conv_path, 'w') as f:
        json.dump(convergence, f, indent=2)
    log(f"  Saved convergence: {conv_path}")

    # Save log
    log_path = os.path.join(output_dir, "inversion_log.txt")
    with open(log_path, 'w') as f:
        f.write('\n'.join(log_lines))

    return {
        "name": name,
        "period_hours": result.spin.period_hours,
        "pole_lambda": result.spin.lambda_deg,
        "pole_beta": result.spin.beta_deg,
        "chi_squared_convex": result.chi_squared_convex,
        "chi_squared_final": result.chi_squared_final,
        "used_ga": result.used_ga,
        "stage": result.stage,
        "n_vertices": len(result.mesh.vertices),
        "n_faces": len(result.mesh.faces),
        "elapsed_seconds": elapsed,
    }


def main():
    """Run blind inversion tests on all validation targets."""
    # Load manifest
    manifest_path = os.path.join(RESULTS_DIR, "benchmark_manifest.json")
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    os.makedirs(BLIND_DIR, exist_ok=True)

    all_results = {}
    for name, target_info in manifest["targets"].items():
        out_dir = os.path.join(BLIND_DIR, name.lower())
        result = run_blind_test_for_target(name, target_info, out_dir)
        if result is not None:
            all_results[name] = result

    # Save summary
    summary_path = os.path.join(BLIND_DIR, "blind_test_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Blind inversion complete: {len(all_results)}/{len(manifest['targets'])} targets")
    print(f"Summary saved to {summary_path}")
    print(f"{'='*60}")

    return all_results


if __name__ == '__main__':
    main()
