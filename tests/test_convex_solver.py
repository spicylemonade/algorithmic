"""
Tests for convex_solver.py

Validates that the convex inversion solver converges on synthetic data
from a known convex shape (ellipsoid) with chi-squared < 0.01 on noise-free data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from forward_model import (create_ellipsoid_mesh, create_sphere_mesh,
                           generate_rotation_lightcurve)
from geometry import SpinState, ecliptic_to_body_matrix
from convex_solver import (LightcurveData, optimize_shape, chi_squared,
                           period_search)

np.random.seed(42)


def make_synthetic_lightcurves(true_mesh, true_spin, n_lcs=3, n_points=50,
                               c_lambert=0.1):
    """Generate synthetic lightcurves from a known shape and spin."""
    lightcurves = []

    # Different viewing geometries (different apparitions)
    sun_dirs_ecl = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.7, 0.7, 0.0]),
        np.array([0.5, 0.3, 0.1]),
    ]

    for i in range(n_lcs):
        sun_ecl = sun_dirs_ecl[i % len(sun_dirs_ecl)]
        sun_ecl /= np.linalg.norm(sun_ecl)
        # Observer slightly offset from sun for non-zero phase angle
        obs_ecl = sun_ecl + np.array([0.05, 0.05, 0.02])
        obs_ecl /= np.linalg.norm(obs_ecl)

        phases, brightness = generate_rotation_lightcurve(
            true_mesh, true_spin, sun_ecl, obs_ecl, n_points=n_points,
            c_lambert=c_lambert
        )

        # Create JD array covering one full rotation
        period_days = true_spin.period_hours / 24.0
        jd_array = true_spin.jd0 + phases / 360.0 * period_days

        # Expand sun/obs to arrays
        sun_arr = np.tile(sun_ecl, (n_points, 1))
        obs_arr = np.tile(obs_ecl, (n_points, 1))

        lc = LightcurveData(
            jd=jd_array,
            brightness=brightness,
            weights=np.ones(n_points),
            sun_ecl=sun_arr,
            obs_ecl=obs_arr
        )
        lightcurves.append(lc)

    return lightcurves


def test_shape_optimization_convergence():
    """Test that shape optimization converges on known ellipsoid data.

    Starting from a sphere, optimize areas to fit lightcurves from an
    ellipsoid. Chi-squared should be very small (< 0.01).
    """
    print("Test: Shape optimization convergence")

    # True shape: mild ellipsoid (1.3:1:0.8) - use low resolution for speed
    true_mesh = create_ellipsoid_mesh(1.3, 1.0, 0.8, n_subdivisions=1)
    true_spin = SpinState(lambda_deg=45, beta_deg=30, period_hours=6.0,
                          jd0=2451545.0)

    # Generate synthetic noise-free data (few points for speed)
    lightcurves = make_synthetic_lightcurves(true_mesh, true_spin, n_lcs=2,
                                            n_points=36, c_lambert=0.1)

    # Start from sphere and optimize (same resolution as true mesh)
    sphere = create_sphere_mesh(n_subdivisions=1)
    opt_mesh, chi2, history = optimize_shape(
        sphere, true_spin, lightcurves, c_lambert=0.1, reg_weight=0.001,
        max_iter=300, verbose=True
    )

    print(f"  Final chi-squared: {chi2:.8f}")
    print(f"  Number of history points: {len(history)}")

    assert chi2 < 0.01, f"Chi-squared too large: {chi2:.6f} (need < 0.01)"
    print("PASS: Shape optimization converges with chi2 < 0.01")


def test_period_search_finds_correct_period():
    """Test that period search identifies the correct period."""
    print("\nTest: Period search")

    true_mesh = create_ellipsoid_mesh(1.5, 1.0, 0.9, n_subdivisions=1)
    true_period = 6.0
    true_spin = SpinState(lambda_deg=0, beta_deg=45, period_hours=true_period,
                          jd0=2451545.0)

    lightcurves = make_synthetic_lightcurves(true_mesh, true_spin, n_lcs=2,
                                            n_points=36, c_lambert=0.1)

    sphere = create_sphere_mesh(n_subdivisions=1)
    base_spin = SpinState(lambda_deg=0, beta_deg=45, period_hours=6.0,
                          jd0=2451545.0)

    best_period, periods, chi2_landscape = period_search(
        sphere, base_spin, lightcurves,
        p_min=5.5, p_max=6.5, n_periods=11,
        c_lambert=0.1, reg_weight=0.001, opt_iter=30, verbose=True
    )

    error = abs(best_period - true_period)
    print(f"  True period: {true_period:.4f} h")
    print(f"  Found period: {best_period:.4f} h")
    print(f"  Error: {error:.6f} h")

    # Period should be found within the search resolution
    step = (6.5 - 5.5) / 20
    assert error < step * 2, f"Period error too large: {error:.4f} h"
    print("PASS: Period search finds correct period")


if __name__ == '__main__':
    print("=" * 60)
    print("Convex Solver Tests")
    print("=" * 60)
    test_shape_optimization_convergence()
    test_period_search_finds_correct_period()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
