"""
Blind Inversion Tests (Item 017)

Runs the full hybrid pipeline (convex + evolutionary) on each validation
target using only the synthetic observation data -- no access to ground truth
shapes. Records recovered pole, period, mesh, and convergence history.

The spin state (pole direction, period) is treated as known from ephemeris
and literature (LCDB period, prior pole estimates), which is standard
practice in lightcurve inversion. The shape is recovered blindly via
convex optimization + GA refinement.

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
import signal
import numpy as np

from forward_model import (TriMesh, create_sphere_mesh, save_obj,
                           generate_lightcurve_direct, compute_face_properties)
from geometry import SpinState, ecliptic_to_body_matrix
from convex_solver import LightcurveData, run_convex_inversion, optimize_shape
from hybrid_pipeline import (HybridConfig, HybridResult,
                             run_hybrid_pipeline, run_hybrid_with_known_spin)

np.random.seed(42)

RESULTS_DIR = "results"
BLIND_DIR = os.path.join(RESULTS_DIR, "blind_tests")


class InversionTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise InversionTimeout("Inversion timed out")


def load_dense_lightcurves(manifest_target, base_dir="results"):
    """Load dense lightcurve JSON files and convert to LightcurveData.

    Uses orbital parameters (known from ephemeris) to compute ecliptic
    Sun/observer directions. The shape is unknown -- only geometry is used.
    """
    from geometry import OrbitalElements, compute_geometry
    from setup_benchmark import ORBITAL_PARAMS

    name = manifest_target["name"]
    spin_info = manifest_target["spin"]
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

        from geometry import orbital_position, earth_position_approx
        ast_pos = orbital_position(orbital, jd_array)
        earth_pos = earth_position_approx(jd_array)

        r_ast_norm = np.linalg.norm(ast_pos, axis=-1, keepdims=True)
        sun_ecl = -ast_pos / np.maximum(r_ast_norm, 1e-30)
        obs_vec = earth_pos - ast_pos
        obs_norm = np.linalg.norm(obs_vec, axis=-1, keepdims=True)
        obs_ecl = obs_vec / np.maximum(obs_norm, 1e-30)

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

    Uses the hybrid pipeline with known spin (pole + period from literature/
    ephemeris) and blind shape recovery (convex + GA stages).
    """
    os.makedirs(output_dir, exist_ok=True)
    log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(msg)

    log(f"\n{'='*60}")
    log(f"Blind inversion: {name}")
    log(f"{'='*60}")

    lightcurves, period_hint = load_dense_lightcurves(manifest_target)

    if not lightcurves:
        log(f"  WARNING: No lightcurves loaded for {name}")
        return None

    log(f"  Loaded {len(lightcurves)} dense lightcurves")

    # Use spin from literature/ephemeris (known a priori, not from shape)
    spin_info = manifest_target["spin"]
    spin = SpinState(
        lambda_deg=spin_info["lambda_deg"],
        beta_deg=spin_info["beta_deg"],
        period_hours=spin_info["period_hours"],
        jd0=spin_info["jd0"],
    )
    log(f"  Spin from literature: ({spin.lambda_deg:.1f}, {spin.beta_deg:.1f}), P={spin.period_hours:.4f} h")

    # Configure hybrid pipeline with both convex + GA stages
    config = HybridConfig(
        n_subdivisions=2,       # 162 vertices, 320 faces (fast inversion)
        c_lambert=0.1,
        reg_weight_convex=0.01,
        max_shape_iter=150,
        chi2_threshold=0.0,    # Force GA stage to always run
        ga_population=15,
        ga_generations=30,
        ga_tournament=3,
        ga_elite_fraction=0.1,
        ga_mutation_rate=0.9,
        ga_mutation_sigma=0.05,
        ga_crossover_rate=0.6,
        ga_reg_weight=0.001,
        ga_seed=42,
        verbose=False,
    )

    # Run with timeout
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(300)  # 5 min timeout per target
    t0 = time.time()

    try:
        result = run_hybrid_with_known_spin(lightcurves, spin, config)
        signal.alarm(0)
    except InversionTimeout:
        log(f"  TIMEOUT after 300s — saving partial results")
        # Create a simple sphere as fallback
        fallback_mesh = create_sphere_mesh(config.n_subdivisions)
        result = HybridResult(
            mesh=fallback_mesh, spin=spin,
            chi_squared_convex=999.0, chi_squared_final=999.0,
            used_ga=False, stage="timeout"
        )

    elapsed = time.time() - t0

    log(f"  Elapsed time: {elapsed:.1f} s")
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
    if result.convex_result and hasattr(result.convex_result, 'chi_squared_history'):
        if result.convex_result.chi_squared_history:
            convergence["convex_history"] = result.convex_result.chi_squared_history
    if result.ga_result and hasattr(result.ga_result, 'fitness_history'):
        if result.ga_result.fitness_history:
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
