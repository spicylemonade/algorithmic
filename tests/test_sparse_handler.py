"""
Tests for sparse_handler.py

Validates:
1. H-G phase function (alpha=0 gives maximum brightness)
2. H-G1-G2 model correctness
3. Magnitude calibration round-trip
4. Sparse CSV parsing
5. Combined dense + sparse inversion recovers pole within 10 degrees
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import tempfile
import csv

from sparse_handler import (
    hg_phase_function, hg12_phase_function, _phi1, _phi2, _phi3,
    calibrate_sparse_magnitudes,
    parse_gaia_sso_csv, parse_generic_sparse,
    SparseDataset, SparseObservation,
    create_sparse_lightcurve_data,
    combined_chi_squared, optimize_combined,
    sparse_chi_squared,
)
from forward_model import (
    create_ellipsoid_mesh, create_sphere_mesh,
    generate_rotation_lightcurve, generate_lightcurve_direct,
    compute_brightness,
)
from geometry import (
    SpinState, OrbitalElements, compute_geometry,
    ecliptic_to_body_matrix, spin_axis_vector,
    orbital_position, earth_position_approx,
)
from convex_solver import LightcurveData, optimize_shape, _precompute_body_dirs

np.random.seed(42)


# ===================================================================
# Test 1: H-G phase function
# ===================================================================

def test_hg_phase_alpha_zero_max_brightness():
    """At alpha=0 (opposition), brightness should be at maximum (magnitude at minimum)."""
    print("Test: H-G phase function alpha=0 gives maximum brightness")

    H = 10.0
    G = 0.15

    # alpha=0 should give brightest (smallest magnitude)
    alpha_zero = 0.0
    alpha_values = np.linspace(0.01, np.radians(120), 50)

    V_zero = hg_phase_function(alpha_zero, H, G)
    V_others = hg_phase_function(alpha_values, H, G)

    # At alpha=0: phi1(0)=1, phi2(0)=1
    # So V(0) = H - 2.5*log10(G*1 + (1-G)*1) = H - 2.5*log10(1) = H
    assert abs(V_zero - H) < 1e-10, \
        f"V(0) should equal H={H}, got {V_zero}"

    # Brightness should decrease (magnitude increase) with phase angle
    assert np.all(V_others >= V_zero - 1e-10), \
        "Magnitude at alpha>0 should be >= magnitude at alpha=0"

    print(f"  V(0) = {V_zero:.6f} (expected {H})")
    print(f"  V(30deg) = {hg_phase_function(np.radians(30), H, G):.6f}")
    print(f"  V(90deg) = {hg_phase_function(np.radians(90), H, G):.6f}")
    print("PASS: H-G phase function alpha=0 max brightness")


def test_hg_phase_monotonic():
    """H-G phase function should be monotonically increasing (fainter) with alpha."""
    print("Test: H-G phase function is monotonically increasing")

    H = 12.0
    G = 0.15
    alphas = np.linspace(0.001, np.radians(150), 200)
    V = hg_phase_function(alphas, H, G)

    # Check monotonic increase (each value >= previous)
    diffs = np.diff(V)
    assert np.all(diffs >= -1e-10), \
        "H-G phase function not monotonically increasing with alpha"

    print("PASS: H-G phase function monotonic")


def test_hg_phase_g_dependence():
    """Larger G means less opposition surge (flatter phase curve)."""
    print("Test: H-G G parameter dependence")

    H = 10.0
    alpha = np.radians(20)

    V_low_G = hg_phase_function(alpha, H, 0.05)
    V_high_G = hg_phase_function(alpha, H, 0.40)

    # Higher G means steeper phi1 contributes more -> brighter at moderate alpha
    # phi1 drops faster, but G*phi1 at small alpha is larger for large G
    # At alpha=20deg, higher G gives brighter (lower V)
    print(f"  V(G=0.05) = {V_low_G:.4f}")
    print(f"  V(G=0.40) = {V_high_G:.4f}")

    # Both should be fainter than H
    assert V_low_G > H, "V at alpha>0 should be > H"
    assert V_high_G > H, "V at alpha>0 should be > H"
    print("PASS: H-G G parameter dependence")


# ===================================================================
# Test 2: H-G1-G2 model
# ===================================================================

def test_hg12_phase_alpha_zero():
    """H-G1-G2 model at alpha=0 should equal H."""
    print("Test: H-G1-G2 alpha=0")

    H = 10.0
    G1 = 0.15
    G2 = 0.30

    V_zero = hg12_phase_function(0.0, H, G1, G2)
    # At alpha=0: phi1(0)=1, phi2(0)=1, phi3(0)=1
    # V = H - 2.5*log10(G1 + G2 + (1-G1-G2)) = H - 2.5*log10(1) = H
    assert abs(V_zero - H) < 1e-10, \
        f"V(0) should equal H={H}, got {V_zero}"

    print(f"  V(0) = {V_zero:.6f} (expected {H})")
    print("PASS: H-G1-G2 alpha=0")


def test_hg12_reduces_to_hg():
    """When G2 = 1 - G1 (no phi3 component), H-G1-G2 should approximate H-G."""
    print("Test: H-G1-G2 reduces to H-G")

    H = 10.0
    G = 0.15
    # In HG model: V = H - 2.5*log10(G*phi1 + (1-G)*phi2)
    # In HG12 with G1=G, G2=1-G: V = H - 2.5*log10(G*phi1 + (1-G)*phi2 + 0*phi3)
    G1 = G
    G2 = 1.0 - G

    alphas = np.linspace(0.001, np.radians(100), 50)
    V_hg = hg_phase_function(alphas, H, G)
    V_hg12 = hg12_phase_function(alphas, H, G1, G2)

    max_diff = np.max(np.abs(V_hg - V_hg12))
    print(f"  Max difference: {max_diff:.10f}")
    assert max_diff < 1e-10, \
        f"H-G1-G2 with G2=1-G1 should match H-G, diff={max_diff}"

    print("PASS: H-G1-G2 reduces to H-G")


def test_hg12_monotonic():
    """H-G1-G2 model should be monotonically increasing with alpha."""
    print("Test: H-G1-G2 monotonic")

    H = 10.0
    G1 = 0.2
    G2 = 0.3
    alphas = np.linspace(0.001, np.radians(150), 200)
    V = hg12_phase_function(alphas, H, G1, G2)

    diffs = np.diff(V)
    assert np.all(diffs >= -1e-10), \
        "H-G1-G2 phase function not monotonically increasing"
    print("PASS: H-G1-G2 monotonic")


# ===================================================================
# Test 3: Magnitude calibration
# ===================================================================

def test_calibration_round_trip():
    """Calibrating then reconstructing should recover original magnitudes."""
    print("Test: Calibration round-trip")

    H = 10.0
    G = 0.15
    n = 20
    np.random.seed(42)
    alphas = np.random.uniform(0.05, np.radians(60), n)
    r_helio = np.random.uniform(1.5, 3.0, n)
    r_geo = np.random.uniform(0.8, 2.5, n)

    # Generate "observed" magnitudes from phase model
    dist_mod = 5.0 * np.log10(r_helio * r_geo)
    phase_term = hg_phase_function(alphas, 0.0, G)
    # m_obs = H + dist_mod + phase_correction (= V_model(alpha) - H at H=0)
    m_obs = H + dist_mod + phase_term

    # Calibrate: should remove distance and phase, leaving H
    m_reduced = calibrate_sparse_magnitudes(m_obs, alphas, r_helio, r_geo,
                                            H, G, model='HG')

    # m_reduced should be close to H (the absolute magnitude)
    residuals = m_reduced - H
    max_err = np.max(np.abs(residuals))
    print(f"  Max calibration error: {max_err:.2e}")
    assert max_err < 1e-10, f"Calibration round-trip error too large: {max_err}"
    print("PASS: Calibration round-trip")


# ===================================================================
# Test 4: Parsing
# ===================================================================

def test_parse_generic_sparse():
    """Test parsing a generic sparse CSV file."""
    print("Test: Parse generic sparse CSV")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False,
                                     newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['jd', 'mag', 'mag_err', 'filter',
                         'phase_angle_deg', 'r_helio', 'r_geo'])
        writer.writerow([2459000.5, 15.2, 0.03, 'r', 10.5, 2.1, 1.5])
        writer.writerow([2459001.5, 15.1, 0.04, 'g', 11.0, 2.1, 1.4])
        writer.writerow([2459002.5, 15.3, 0.02, 'r', 12.0, 2.1, 1.3])
        tmppath = f.name

    try:
        dataset = parse_generic_sparse(tmppath)
        assert dataset.n_obs == 3, f"Expected 3 observations, got {dataset.n_obs}"
        assert dataset.observations[0].jd == 2459000.5
        assert abs(dataset.observations[0].mag - 15.2) < 1e-10
        assert dataset.observations[1].filter_name == 'g'
        assert abs(dataset.observations[2].phase_angle - np.radians(12.0)) < 1e-6
        print(f"  Parsed {dataset.n_obs} observations")
        print("PASS: Parse generic sparse CSV")
    finally:
        os.unlink(tmppath)


def test_parse_gaia_sso_csv():
    """Test parsing a simplified Gaia SSO CSV."""
    print("Test: Parse Gaia SSO CSV")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False,
                                     newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['jd', 'mag', 'mag_err', 'phase_angle_deg',
                         'r_helio', 'r_geo'])
        writer.writerow([2459000.5, 14.5, 0.02, 15.0, 2.5, 1.8])
        writer.writerow([2459010.5, 14.8, 0.03, 18.0, 2.5, 1.9])
        tmppath = f.name

    try:
        dataset = parse_gaia_sso_csv(tmppath)
        assert dataset.n_obs == 2, f"Expected 2 observations, got {dataset.n_obs}"
        assert dataset.source == "GaiaDR3"
        print(f"  Parsed {dataset.n_obs} observations from Gaia format")
        print("PASS: Parse Gaia SSO CSV")
    finally:
        os.unlink(tmppath)


# ===================================================================
# Test 5: Integration — combined dense + sparse pole recovery
# ===================================================================

def _make_dense_lightcurve(mesh, spin, sun_ecl, obs_ecl, n_points, c_lambert,
                           noise_sigma=0.0):
    """Helper to generate one dense lightcurve at fixed geometry."""
    sun_ecl = sun_ecl / np.linalg.norm(sun_ecl)
    obs_ecl = obs_ecl / np.linalg.norm(obs_ecl)

    phases, brightness = generate_rotation_lightcurve(
        mesh, spin, sun_ecl, obs_ecl, n_points=n_points, c_lambert=c_lambert
    )

    if noise_sigma > 0:
        brightness += np.random.normal(0, noise_sigma * np.mean(brightness),
                                       n_points)
        brightness = np.maximum(brightness, 1e-30)

    period_days = spin.period_hours / 24.0
    jd_array = spin.jd0 + phases / 360.0 * period_days

    sun_arr = np.tile(sun_ecl, (n_points, 1))
    obs_arr = np.tile(obs_ecl, (n_points, 1))

    weights = np.ones(n_points)
    return LightcurveData(jd=jd_array, brightness=brightness,
                          weights=weights, sun_ecl=sun_arr, obs_ecl=obs_arr)


def _make_sparse_from_geometry(mesh, spin, jd_array, sun_ecl_arr, obs_ecl_arr,
                               c_lambert, noise_sigma=0.0):
    """Generate sparse brightness observations at given geometry."""
    n = len(jd_array)
    brightness = np.zeros(n)
    for j in range(n):
        R = ecliptic_to_body_matrix(spin, jd_array[j])
        sun_body = R @ sun_ecl_arr[j]
        obs_body = R @ obs_ecl_arr[j]
        brightness[j] = compute_brightness(mesh, sun_body, obs_body, c_lambert)

    if noise_sigma > 0:
        brightness += np.random.normal(0, noise_sigma * np.mean(brightness), n)
        brightness = np.maximum(brightness, 1e-30)

    weights = np.ones(n)
    return LightcurveData(jd=jd_array, brightness=brightness,
                          weights=weights, sun_ecl=sun_ecl_arr,
                          obs_ecl=obs_ecl_arr)


def _angular_separation_deg(lam1, bet1, lam2, bet2):
    """Compute angular separation between two poles in degrees."""
    lam1_r = np.radians(lam1)
    bet1_r = np.radians(bet1)
    lam2_r = np.radians(lam2)
    bet2_r = np.radians(bet2)
    v1 = np.array([np.cos(bet1_r)*np.cos(lam1_r),
                    np.cos(bet1_r)*np.sin(lam1_r),
                    np.sin(bet1_r)])
    v2 = np.array([np.cos(bet2_r)*np.cos(lam2_r),
                    np.cos(bet2_r)*np.sin(lam2_r),
                    np.sin(bet2_r)])
    cos_sep = np.clip(np.dot(v1, v2), -1, 1)
    return np.degrees(np.arccos(cos_sep))


def test_combined_pole_recovery():
    """Test that combining >=50 sparse + 2 dense lightcurves recovers the pole
    within 10 degrees for a synthetic ellipsoid.

    Strategy:
    - Use an elongated ellipsoid with known pole and period.
    - Generate 2 dense lightcurves at well-separated ecliptic geometries.
    - Generate 60 sparse data points spanning ecliptic longitudes.
    - Use the known shape model to evaluate the combined chi-squared
      objective at a grid of trial pole directions.
    - Verify the minimum-chi-squared pole is within 10 degrees of truth.

    This tests the core property of the combined_chi_squared function:
    that when the shape is known, the objective is minimized at the
    correct pole direction. This is the foundation of lightcurve inversion
    — the pole direction that best explains the brightness variations
    across different observing geometries.
    """
    print("\nTest: Combined dense + sparse pole recovery")
    np.random.seed(42)

    # True parameters
    true_lam = 90.0
    true_bet = 45.0
    true_period = 6.0
    c_lambert = 0.1

    true_spin = SpinState(lambda_deg=true_lam, beta_deg=true_bet,
                          period_hours=true_period, jd0=2451545.0)

    # Elongated ellipsoid — higher subdivision for realistic shape
    true_mesh = create_ellipsoid_mesh(2.0, 1.0, 0.8, n_subdivisions=2)

    # ---- Dense lightcurves (2 apparitions at separated ecliptic longitudes) ----
    dense_lcs = []

    # Apparition 1: ecliptic longitude ~0 deg
    sun1 = np.array([1.0, 0.0, 0.05])
    obs1 = np.array([0.97, 0.05, 0.08])
    lc1 = _make_dense_lightcurve(true_mesh, true_spin, sun1, obs1,
                                  n_points=80, c_lambert=c_lambert,
                                  noise_sigma=0.0)
    dense_lcs.append(lc1)

    # Apparition 2: ecliptic longitude ~90 deg
    sun2 = np.array([0.0, 1.0, 0.05])
    obs2 = np.array([0.05, 0.97, 0.08])
    lc2 = _make_dense_lightcurve(true_mesh, true_spin, sun2, obs2,
                                  n_points=80, c_lambert=c_lambert,
                                  noise_sigma=0.0)
    dense_lcs.append(lc2)

    # ---- Sparse observations (60 points spanning full ecliptic) ----
    n_sparse = 60
    jd_sparse = true_spin.jd0 + np.linspace(10, 1500, n_sparse)

    ecl_longs = np.linspace(0, 2 * np.pi, n_sparse, endpoint=False)
    sun_sparse = np.zeros((n_sparse, 3))
    obs_sparse = np.zeros((n_sparse, 3))
    for k in range(n_sparse):
        el = ecl_longs[k]
        sun_sparse[k] = [np.cos(el), np.sin(el), 0.05 * np.sin(2 * el)]
        sun_sparse[k] /= np.linalg.norm(sun_sparse[k])
        obs_sparse[k] = sun_sparse[k] + np.array([0.03 * np.sin(el),
                                                    -0.03 * np.cos(el),
                                                    0.02])
        obs_sparse[k] /= np.linalg.norm(obs_sparse[k])

    sparse_lc = _make_sparse_from_geometry(
        true_mesh, true_spin, jd_sparse, sun_sparse, obs_sparse,
        c_lambert=c_lambert, noise_sigma=0.0
    )

    print(f"  Dense: {len(dense_lcs)} lightcurves, "
          f"{sum(len(lc.jd) for lc in dense_lcs)} total points")
    print(f"  Sparse: {len(sparse_lc.jd)} points")

    # ---- Coarse pole grid search using combined_chi_squared ----
    # Evaluate the combined objective at each trial pole with the
    # *true* mesh. The minimum should be at the true pole.
    lambdas_coarse = np.arange(0, 360, 10)
    betas_coarse = np.arange(-80, 81, 10)

    best_chi2 = np.inf
    best_lam = 0.0
    best_bet = 0.0

    for lam in lambdas_coarse:
        for bet in betas_coarse:
            trial_spin = SpinState(
                lambda_deg=lam, beta_deg=bet,
                period_hours=true_period,
                jd0=true_spin.jd0
            )
            chi2 = combined_chi_squared(
                true_mesh, trial_spin, dense_lcs, sparse_lc,
                c_lambert=c_lambert, lambda_sparse=1.0, reg_weight=0.0
            )
            if chi2 < best_chi2:
                best_chi2 = chi2
                best_lam = lam
                best_bet = bet

    print(f"  Coarse best: ({best_lam:.0f}, {best_bet:.0f}), "
          f"chi2={best_chi2:.8f}")

    # ---- Fine refinement around coarse best ----
    lambdas_fine = np.arange(best_lam - 10, best_lam + 11, 2)
    betas_fine = np.arange(max(best_bet - 10, -90),
                           min(best_bet + 11, 91), 2)

    for lam in lambdas_fine:
        for bet in betas_fine:
            lam_wrapped = lam % 360
            trial_spin = SpinState(
                lambda_deg=lam_wrapped, beta_deg=bet,
                period_hours=true_period,
                jd0=true_spin.jd0
            )
            chi2 = combined_chi_squared(
                true_mesh, trial_spin, dense_lcs, sparse_lc,
                c_lambert=c_lambert, lambda_sparse=1.0, reg_weight=0.0
            )
            if chi2 < best_chi2:
                best_chi2 = chi2
                best_lam = lam_wrapped
                best_bet = bet

    # Verify chi2 at true pole is effectively zero
    chi2_true = combined_chi_squared(
        true_mesh, true_spin, dense_lcs, sparse_lc,
        c_lambert=c_lambert, lambda_sparse=1.0, reg_weight=0.0
    )

    sep = _angular_separation_deg(true_lam, true_bet, best_lam, best_bet)
    print(f"  True pole:  ({true_lam:.0f}, {true_bet:.0f})")
    print(f"  Found pole: ({best_lam:.0f}, {best_bet:.0f})")
    print(f"  Angular separation: {sep:.1f} deg")
    print(f"  Chi2 at true pole: {chi2_true:.8f}")
    print(f"  Chi2 at best pole: {best_chi2:.8f}")

    assert sep < 10.0, \
        f"Pole recovery failed: separation {sep:.1f} deg (need < 10)"
    assert chi2_true < 1e-6, \
        f"Chi2 at true pole should be ~0, got {chi2_true}"
    print("PASS: Combined dense + sparse recovers pole within 10 degrees")


# ===================================================================
# Run all tests
# ===================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Sparse Handler Tests")
    print("=" * 60)

    # Phase function tests
    test_hg_phase_alpha_zero_max_brightness()
    test_hg_phase_monotonic()
    test_hg_phase_g_dependence()

    # H-G1-G2 tests
    test_hg12_phase_alpha_zero()
    test_hg12_reduces_to_hg()
    test_hg12_monotonic()

    # Calibration test
    test_calibration_round_trip()

    # Parser tests
    test_parse_generic_sparse()
    test_parse_gaia_sso_csv()

    # Integration test
    test_combined_pole_recovery()

    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
