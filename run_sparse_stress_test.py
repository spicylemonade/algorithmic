#!/usr/bin/env python3
"""
Sparse-Only Inversion Stress Test

Runs sparse-only inversion at decreasing data levels (200, 100, 50, 25 points)
for multiple validation targets and records pole error, period error, and
convergence status.

Output: results/sparse_stress_test.csv
"""

import sys
import os
import json
import csv
import signal
import traceback
import numpy as np
from dataclasses import dataclass
from typing import Optional

# Ensure the repo root is on the path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_ROOT)

from sparse_handler import (
    SparseObservation,
    SparseDataset,
    SparseInversionResult,
    create_sparse_lightcurve_data,
    run_sparse_only_inversion,
)
from setup_benchmark import ORBITAL_PARAMS
from geometry import SpinState


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MANIFEST_PATH = os.path.join(REPO_ROOT, "results", "benchmark_manifest.json")
OBSERVATIONS_DIR = os.path.join(REPO_ROOT, "results", "observations")
OUTPUT_CSV = os.path.join(REPO_ROOT, "results", "sparse_stress_test.csv")

# Validation targets to test (at least 3)
VALIDATION_TARGETS = ["Eros", "Kleopatra", "Gaspra"]

# Data levels (number of sparse points to subsample)
DATA_LEVELS = [200, 100, 50, 25]

# Random seed for reproducible subsampling
SEED = 42

# Inversion timeout in seconds
TIMEOUT_SEC = 120

# Inversion grid parameters (kept modest for stress testing speed)
N_PERIODS = 50
N_LAMBDA = 6
N_BETA = 3
N_SUBDIVISIONS = 1
C_LAMBERT = 0.1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def angular_separation(lam1, bet1, lam2, bet2):
    """Compute angular separation between two pole directions (degrees).

    Parameters
    ----------
    lam1, bet1 : float
        Ecliptic longitude and latitude of first pole (degrees).
    lam2, bet2 : float
        Ecliptic longitude and latitude of second pole (degrees).

    Returns
    -------
    float
        Angular separation in degrees.
    """
    lam1, bet1, lam2, bet2 = [np.radians(x) for x in (lam1, bet1, lam2, bet2)]
    cos_sep = (
        np.sin(bet1) * np.sin(bet2)
        + np.cos(bet1) * np.cos(bet2) * np.cos(lam1 - lam2)
    )
    return np.degrees(np.arccos(np.clip(cos_sep, -1.0, 1.0)))


class TimeoutError(Exception):
    """Raised when an inversion exceeds the allowed wall-clock time."""
    pass


def _timeout_handler(signum, frame):
    raise TimeoutError("Inversion timed out")


def load_sparse_observations(json_path):
    """Load a sparse observation JSON file into a list of dicts.

    The JSON file is expected to contain a list of objects, each with keys:
        jd, mag, mag_err, phase_angle_deg, r_helio, r_geo
    """
    with open(json_path, "r") as f:
        return json.load(f)


def observations_to_dataset(obs_dicts, target_id=""):
    """Convert a list of observation dicts to a SparseDataset."""
    obs_list = []
    for d in obs_dicts:
        obs = SparseObservation(
            jd=d["jd"],
            mag=d["mag"],
            mag_err=d["mag_err"],
            filter_name="V",
            phase_angle=np.radians(d["phase_angle_deg"]),
            r_helio=d["r_helio"],
            r_geo=d["r_geo"],
        )
        obs_list.append(obs)
    return SparseDataset(
        observations=obs_list, source="benchmark", target_id=target_id
    )


def subsample_observations(obs_dicts, n_points, rng):
    """Randomly subsample observation dicts to n_points entries.

    If the data already has <= n_points observations, return all of them.
    """
    if len(obs_dicts) <= n_points:
        return list(obs_dicts)
    indices = rng.choice(len(obs_dicts), size=n_points, replace=False)
    indices.sort()  # preserve temporal order
    return [obs_dicts[i] for i in indices]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load benchmark manifest
    print(f"Loading benchmark manifest from {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    targets_info = manifest["targets"]

    # Validate that all requested targets exist in the manifest
    for name in VALIDATION_TARGETS:
        if name not in targets_info:
            print(f"WARNING: target '{name}' not found in manifest, skipping.")

    results = []
    rng = np.random.default_rng(SEED)

    for target_name in VALIDATION_TARGETS:
        if target_name not in targets_info:
            continue

        info = targets_info[target_name]
        spin_truth = info["spin"]
        true_lambda = spin_truth["lambda_deg"]
        true_beta = spin_truth["beta_deg"]
        true_period = spin_truth["period_hours"]
        jd0 = spin_truth["jd0"]

        # Period search range: +/- 20% around true period
        p_min = true_period * 0.8
        p_max = true_period * 1.2

        # Orbital elements
        orbital = ORBITAL_PARAMS.get(target_name)
        if orbital is None:
            print(f"WARNING: no orbital elements for '{target_name}', skipping.")
            continue

        # Load sparse observation data
        sparse_json_name = info["sparse_observations"]  # e.g. "observations/eros_sparse.json"
        sparse_json_path = os.path.join(REPO_ROOT, "results", sparse_json_name)
        print(f"\nLoading sparse observations for {target_name} from {sparse_json_path}")
        all_obs = load_sparse_observations(sparse_json_path)
        print(f"  Total sparse observations: {len(all_obs)}")

        for n_sparse in DATA_LEVELS:
            print(f"\n  [{target_name}] n_sparse={n_sparse}")

            # Subsample
            sub_obs = subsample_observations(all_obs, n_sparse, rng)
            actual_n = len(sub_obs)
            print(f"    Subsampled to {actual_n} points")

            # Build SparseDataset and convert to LightcurveData
            dataset = observations_to_dataset(sub_obs, target_id=target_name)
            spin_ref = SpinState(
                lambda_deg=true_lambda,
                beta_deg=true_beta,
                period_hours=true_period,
                jd0=jd0,
            )
            try:
                lc_data = create_sparse_lightcurve_data(dataset, orbital, spin_ref)
            except Exception as exc:
                print(f"    ERROR creating LightcurveData: {exc}")
                results.append({
                    "target": target_name,
                    "n_sparse": actual_n,
                    "pole_error_deg": float("nan"),
                    "period_error_hr": float("nan"),
                    "converged": False,
                })
                continue

            # Run sparse-only inversion with timeout
            converged = True
            pole_error = float("nan")
            period_error = float("nan")

            try:
                # Set alarm-based timeout (POSIX only)
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(TIMEOUT_SEC)

                inv_result = run_sparse_only_inversion(
                    sparse_lc=lc_data,
                    orbital_elements=orbital,
                    p_min=p_min,
                    p_max=p_max,
                    n_periods=N_PERIODS,
                    n_lambda=N_LAMBDA,
                    n_beta=N_BETA,
                    n_subdivisions=N_SUBDIVISIONS,
                    c_lambert=C_LAMBERT,
                    verbose=False,
                )

                # Cancel alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

                # Compute errors
                pole_error = angular_separation(
                    inv_result.pole_lambda,
                    inv_result.pole_beta,
                    true_lambda,
                    true_beta,
                )
                period_error = abs(inv_result.period_hours - true_period)

                print(
                    f"    Recovered: period={inv_result.period_hours:.4f} h, "
                    f"pole=({inv_result.pole_lambda:.1f}, {inv_result.pole_beta:.1f})"
                )
                print(
                    f"    Errors: pole={pole_error:.2f} deg, "
                    f"period={period_error:.4f} hr"
                )

            except TimeoutError:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                converged = False
                print(f"    TIMEOUT after {TIMEOUT_SEC}s")

            except Exception as exc:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                converged = False
                print(f"    ERROR during inversion: {exc}")
                traceback.print_exc()

            results.append({
                "target": target_name,
                "n_sparse": actual_n,
                "pole_error_deg": pole_error,
                "period_error_hr": period_error,
                "converged": converged,
            })

    # Write results CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    print(f"\nWriting results to {OUTPUT_CSV}")
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["target", "n_sparse", "pole_error_deg",
                           "period_error_hr", "converged"]
        )
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    # Summary
    print("\n" + "=" * 60)
    print("SPARSE STRESS TEST SUMMARY")
    print("=" * 60)
    print(f"{'Target':<12} {'N_sparse':>8} {'Pole err (deg)':>15} "
          f"{'Period err (hr)':>16} {'Converged':>10}")
    print("-" * 60)
    for row in results:
        pe = row["pole_error_deg"]
        pre = row["period_error_hr"]
        pe_str = f"{pe:.2f}" if not np.isnan(pe) else "N/A"
        pre_str = f"{pre:.4f}" if not np.isnan(pre) else "N/A"
        conv_str = "Yes" if row["converged"] else "No"
        print(f"{row['target']:<12} {row['n_sparse']:>8} {pe_str:>15} "
              f"{pre_str:>16} {conv_str:>10}")
    print("=" * 60)
    print(f"\nResults saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
