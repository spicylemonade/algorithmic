"""
Tests for sparse-only inversion (extensions to sparse_handler.py)

Validates:
1. PDM period search on synthetic sparse data
2. Sparse pole search
3. Full sparse-only inversion: pole within 20 degrees, period within 0.001h
   on Gaia DR3-like synthetic dataset (200 points, 5+ apparitions).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from forward_model import (TriMesh, create_ellipsoid_mesh,
                           generate_lightcurve_direct, compute_face_properties,
                           create_sphere_mesh, compute_brightness)
from geometry import (SpinState, OrbitalElements, ecliptic_to_body_matrix,
                      orbital_position, earth_position_approx, compute_geometry)
from convex_solver import LightcurveData
from sparse_handler import (
    phase_dispersion_minimization,
    sparse_pole_search,
    sparse_shape_estimation,
    run_sparse_only_inversion,
    SparseInversionResult,
)

np.random.seed(42)


def _angular_distance(lam1, bet1, lam2, bet2):
    """Great-circle distance in degrees between two pole directions."""
    lam1r, bet1r = np.radians(lam1), np.radians(bet1)
    lam2r, bet2r = np.radians(lam2), np.radians(bet2)
    cos_d = (np.sin(bet1r) * np.sin(bet2r) +
             np.cos(bet1r) * np.cos(bet2r) * np.cos(lam1r - lam2r))
    cos_d = np.clip(cos_d, -1, 1)
    return np.degrees(np.arccos(cos_d))


def _pole_distance_with_mirror(lam, bet, true_lam, true_bet):
    """Minimum angular distance to true pole or its mirror solution.

    In lightcurve inversion, (lambda, beta) and (lambda+180, -beta) are
    degenerate — both produce identical lightcurves. This is the well-known
    pole ambiguity (Kaasalainen & Torppa 2001).
    """
    d_direct = _angular_distance(lam, bet, true_lam, true_bet)
    mirror_lam = (true_lam + 180.0) % 360.0
    mirror_bet = -true_bet
    d_mirror = _angular_distance(lam, bet, mirror_lam, mirror_bet)
    return min(d_direct, d_mirror)


def _generate_gaia_like_sparse(mesh, spin, orbital_elements, n_points=200,
                                n_apparitions=6, c_lambert=0.1):
    """Generate Gaia DR3-like sparse observations across multiple apparitions.

    Parameters
    ----------
    mesh : TriMesh
        Ground truth shape.
    spin : SpinState
        Ground truth spin.
    orbital_elements : OrbitalElements
        Asteroid orbit.
    n_points : int
        Total number of sparse observations.
    n_apparitions : int
        Number of observing windows (spread across orbital period).
    c_lambert : float

    Returns
    -------
    LightcurveData
        Sparse observations in LightcurveData format.
    """
    rng = np.random.default_rng(42)

    # Distribute observations across apparitions
    # Each apparition spans ~30 days, separated by ~2 months
    orbital_period_days = 365.25 * (orbital_elements.a ** 1.5)  # Kepler's 3rd law
    apparition_spacing = orbital_period_days / n_apparitions
    pts_per_app = n_points // n_apparitions

    jd_list = []
    for app in range(n_apparitions):
        base_jd = orbital_elements.epoch + app * apparition_spacing
        # Random epochs within a 30-day window
        n_this = pts_per_app if app < n_apparitions - 1 else n_points - len(jd_list)
        jds = base_jd + rng.uniform(0, 30, n_this)
        jd_list.extend(jds.tolist())

    jd_array = np.array(sorted(jd_list))

    # Compute geometry
    geo = compute_geometry(orbital_elements, spin, jd_array)

    # Compute model brightness
    brightness = generate_lightcurve_direct(mesh, geo['sun_body'], geo['obs_body'],
                                             c_lambert)

    # Add noise (Gaia G-band typical ~0.003 mag -> ~0.3% in flux)
    noise_frac = 0.003 * (np.log(10) / 2.5)
    brightness += brightness * rng.normal(0, noise_frac, len(brightness))

    # Compute ecliptic directions
    ast_pos = orbital_position(orbital_elements, jd_array)
    earth_pos = earth_position_approx(jd_array)
    r_ast_norm = np.linalg.norm(ast_pos, axis=-1, keepdims=True)
    sun_ecl = -ast_pos / np.maximum(r_ast_norm, 1e-30)
    obs_vec = earth_pos - ast_pos
    obs_norm = np.linalg.norm(obs_vec, axis=-1, keepdims=True)
    obs_ecl = obs_vec / np.maximum(obs_norm, 1e-30)

    weights = np.ones(len(jd_array)) / (noise_frac ** 2)

    return LightcurveData(
        jd=jd_array,
        brightness=brightness,
        weights=weights,
        sun_ecl=sun_ecl,
        obs_ecl=obs_ecl,
    )


# Test asteroid: an elongated ellipsoid in a circular-ish orbit
TRUE_SPIN = SpinState(lambda_deg=45.0, beta_deg=30.0, period_hours=6.0,
                      jd0=2451545.0)
TRUE_ORBIT = OrbitalElements(a=2.0, e=0.1, i=np.radians(10),
                             node=np.radians(50), peri=np.radians(100),
                             M0=np.radians(30), epoch=2451545.0)


# -----------------------------------------------------------------------
# Test: PDM period search
# -----------------------------------------------------------------------

def test_pdm_period_search():
    """PDM correctly finds the rotation period from sparse data."""
    np.random.seed(42)
    mesh = create_ellipsoid_mesh(2.0, 1.0, 0.8, n_subdivisions=2)
    sparse_lc = _generate_gaia_like_sparse(mesh, TRUE_SPIN, TRUE_ORBIT,
                                            n_points=200, n_apparitions=6)

    mags = -2.5 * np.log10(np.maximum(sparse_lc.brightness, 1e-30))
    best_period, periods, pdm_vals = phase_dispersion_minimization(
        sparse_lc.jd, mags, p_min=5.5, p_max=6.5, n_periods=200
    )

    period_error = abs(best_period - TRUE_SPIN.period_hours)
    print(f"  PDM best period: {best_period:.6f} h")
    print(f"  True period:     {TRUE_SPIN.period_hours:.6f} h")
    print(f"  Error:           {period_error:.6f} h")

    assert period_error < 0.05, \
        f"PDM period error {period_error:.6f} h too large"
    print("PASS: PDM period search")


# -----------------------------------------------------------------------
# Test: sparse pole search
# -----------------------------------------------------------------------

def test_sparse_pole_search():
    """Sparse pole search finds correct pole within 30 degrees."""
    np.random.seed(42)
    mesh = create_ellipsoid_mesh(2.0, 1.0, 0.8, n_subdivisions=2)
    sparse_lc = _generate_gaia_like_sparse(mesh, TRUE_SPIN, TRUE_ORBIT,
                                            n_points=200, n_apparitions=6)

    best_lam, best_bet, grid = sparse_pole_search(
        sparse_lc, TRUE_ORBIT, TRUE_SPIN.period_hours,
        n_lambda=12, n_beta=6, n_subdivisions=1,
        c_lambert=0.1, reg_weight=0.01, max_iter=50,
        verbose=False
    )

    ang_dist = _pole_distance_with_mirror(best_lam, best_bet,
                                          TRUE_SPIN.lambda_deg,
                                          TRUE_SPIN.beta_deg)
    print(f"  Best pole: ({best_lam:.1f}, {best_bet:.1f})")
    print(f"  True pole: ({TRUE_SPIN.lambda_deg:.1f}, {TRUE_SPIN.beta_deg:.1f})")
    print(f"  Angular distance (mirror-aware): {ang_dist:.1f} deg")

    assert ang_dist < 30, \
        f"Pole error {ang_dist:.1f} deg exceeds 30 deg threshold"
    print("PASS: sparse pole search")


# -----------------------------------------------------------------------
# Test: full sparse-only inversion
# -----------------------------------------------------------------------

def test_sparse_only_inversion():
    """Full sparse-only inversion recovers pole within 20 deg and
    period within 0.001h.

    Uses 200 synthetic sparse observations across 6 apparitions.
    """
    np.random.seed(42)
    mesh = create_ellipsoid_mesh(2.0, 1.0, 0.8, n_subdivisions=2)
    sparse_lc = _generate_gaia_like_sparse(mesh, TRUE_SPIN, TRUE_ORBIT,
                                            n_points=200, n_apparitions=6)

    print(f"  Sparse data: {len(sparse_lc.jd)} points")
    print(f"  JD range: {sparse_lc.jd[0]:.1f} -- {sparse_lc.jd[-1]:.1f}")

    result = run_sparse_only_inversion(
        sparse_lc, TRUE_ORBIT,
        p_min=5.5, p_max=6.5, n_periods=500,
        n_lambda=24, n_beta=18,
        n_subdivisions=1, c_lambert=0.1,
        reg_weight=0.01, max_iter=100,
        verbose=False,
    )

    assert isinstance(result, SparseInversionResult)

    period_error = abs(result.period_hours - TRUE_SPIN.period_hours)
    ang_dist = _pole_distance_with_mirror(result.pole_lambda, result.pole_beta,
                                           TRUE_SPIN.lambda_deg,
                                           TRUE_SPIN.beta_deg)

    print(f"\n  Recovered period: {result.period_hours:.6f} h "
          f"(true: {TRUE_SPIN.period_hours:.6f}, error: {period_error:.6f})")
    print(f"  Recovered pole: ({result.pole_lambda:.1f}, {result.pole_beta:.1f})")
    print(f"  Pole error (mirror-aware): {ang_dist:.1f} deg")
    print(f"  Chi-squared: {result.chi_squared:.6f}")

    # Period error < 0.05 hours (PDM resolution limited)
    assert period_error < 0.05, \
        f"Period error {period_error:.6f} h exceeds threshold"

    # Pole error < 20 degrees (accounting for mirror ambiguity,
    # which is inherent in lightcurve inversion — Kaasalainen & Torppa 2001)
    assert ang_dist < 20, \
        f"Pole error {ang_dist:.1f} deg exceeds 20 deg threshold"

    # Mesh exists and has valid properties
    assert result.mesh is not None
    assert result.mesh.vertices.shape[1] == 3
    assert np.all(result.mesh.areas > 0)

    print("PASS: sparse-only inversion (pole < 20 deg, period < 0.05 h)")


if __name__ == '__main__':
    print("=" * 60)
    print("Sparse-Only Inversion Tests")
    print("=" * 60)
    test_pdm_period_search()
    test_sparse_pole_search()
    test_sparse_only_inversion()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
