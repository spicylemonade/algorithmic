"""
Tests for forward_model.py and geometry.py

Validates:
1. Sphere lightcurve is flat/constant
2. Ellipsoid amplitude matches a/b ratio within 2%
3. Kepler equation solver accuracy
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from forward_model import (create_sphere_mesh, create_ellipsoid_mesh,
                           generate_rotation_lightcurve, compute_brightness,
                           TriMesh, compute_face_properties)
from geometry import SpinState, solve_kepler

np.random.seed(42)


def test_kepler_solver():
    """Test Kepler equation solver on known cases."""
    # Circular orbit: E = M
    M = np.linspace(0, 2*np.pi, 100)
    E = solve_kepler(M, 0.0)
    assert np.allclose(E, M, atol=1e-12), "Kepler solver failed for e=0"

    # Known case: e=0.5, M=1.0
    E = solve_kepler(1.0, 0.5)
    # Verify: M = E - e*sin(E)
    M_check = E - 0.5 * np.sin(E)
    assert abs(M_check - 1.0) < 1e-12, f"Kepler solver failed: M_check={M_check}"

    print("PASS: Kepler solver")


def test_sphere_constant_brightness():
    """A sphere should produce a constant lightcurve (no rotational variation)."""
    sphere = create_sphere_mesh(n_subdivisions=3)
    spin = SpinState(lambda_deg=0, beta_deg=45, period_hours=6.0, jd0=2451545.0)

    # Sun at (1,0,0) ecliptic, observer at (0.8, 0.2, 0.1) ecliptic
    sun_ecl = np.array([1.0, 0.0, 0.0])
    sun_ecl /= np.linalg.norm(sun_ecl)
    obs_ecl = np.array([0.8, 0.2, 0.1])
    obs_ecl /= np.linalg.norm(obs_ecl)

    phases, brightness = generate_rotation_lightcurve(
        sphere, spin, sun_ecl, obs_ecl, n_points=200
    )

    # Brightness should be constant (sphere is rotationally symmetric)
    std = np.std(brightness)
    mean = np.mean(brightness)
    relative_variation = std / mean

    print(f"  Sphere relative variation: {relative_variation:.6f}")
    assert relative_variation < 0.01, \
        f"Sphere brightness variation too large: {relative_variation:.4f}"
    print("PASS: Sphere constant brightness")


def test_ellipsoid_amplitude():
    """Ellipsoid lightcurve amplitude should match a/b axis ratio within 2%.

    For Lambert scattering at zero phase angle (opposition), equator-on view,
    the brightness is proportional to the projected cross-sectional area.
    A triaxial ellipsoid (a, b, c) with rotation about z-axis produces a
    lightcurve whose max/min brightness ratio equals a/b (since the
    projected area alternates between pi*a*c and pi*b*c).

    We use c_lambert=1.0 (pure Lambert) for this analytical test, since
    the Lambert law gives brightness proportional to projected area.
    """
    a_axis, b_axis, c_axis = 2.0, 1.0, 1.0
    ellipsoid = create_ellipsoid_mesh(a_axis, b_axis, c_axis, n_subdivisions=4)

    # Pole along z, view from equator (x-y plane)
    spin = SpinState(lambda_deg=0, beta_deg=90, period_hours=6.0, jd0=2451545.0)

    # Sun and observer both in the ecliptic plane (equator-on for pole at z)
    sun_ecl = np.array([1.0, 0.0, 0.0])
    obs_ecl = np.array([1.0, 0.0, 0.0])  # zero phase angle (opposition)

    # Use pure Lambert scattering for analytical validation
    phases, brightness = generate_rotation_lightcurve(
        ellipsoid, spin, sun_ecl, obs_ecl, n_points=720, c_lambert=1.0
    )

    max_b = np.max(brightness)
    min_b = np.min(brightness)
    amplitude_ratio = max_b / min_b

    # For Lambert scattering at opposition, brightness = sum(A_k * mu_k^2)
    # which is proportional to projected area. The ratio of max to min
    # projected area for an (a, b, c) ellipsoid rotating about z,
    # viewed equator-on, is a/b.
    expected_ratio = a_axis / b_axis
    error_pct = abs(amplitude_ratio - expected_ratio) / expected_ratio * 100

    print(f"  Ellipsoid max/min brightness ratio: {amplitude_ratio:.4f}")
    print(f"  Expected a/b ratio: {expected_ratio:.4f}")
    print(f"  Error: {error_pct:.2f}%")

    assert error_pct < 2.0, \
        f"Ellipsoid amplitude error too large: {error_pct:.2f}% (need <2%)"
    print("PASS: Ellipsoid amplitude matches a/b ratio within 2%")


def test_mesh_properties():
    """Test face normal and area computation."""
    # Simple tetrahedron
    vertices = np.array([
        [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
    ], dtype=np.float64)
    faces = np.array([
        [0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]
    ], dtype=np.int64)
    normals, areas = compute_face_properties(vertices, faces)

    # Each face should have non-zero area
    assert np.all(areas > 0), "Some face areas are zero"
    # Normals should be unit vectors
    norm_lengths = np.linalg.norm(normals, axis=1)
    assert np.allclose(norm_lengths, 1.0, atol=1e-10), "Normals not unit length"
    print("PASS: Mesh properties")


def test_brightness_zero_for_back_illumination():
    """Brightness should be zero if Sun illuminates back of all facets."""
    sphere = create_sphere_mesh(n_subdivisions=2)
    # Sun and observer on exactly opposite sides — some facets visible, none illuminated from front
    # Actually for a sphere, half is always visible. Let's test with sun behind.
    # Use a single-face mesh for definitive test
    vertices = np.array([[0,0,0], [1,0,0], [0,1,0]], dtype=np.float64)
    faces = np.array([[0,1,2]], dtype=np.int64)
    normals, areas = compute_face_properties(vertices, faces)
    mesh = TriMesh(vertices=vertices, faces=faces, normals=normals, areas=areas)

    # Normal points in +z direction; sun from -z (behind the face)
    sun_dir = np.array([0, 0, -1.0])
    obs_dir = np.array([0, 0, 1.0])  # observer sees front

    b = compute_brightness(mesh, sun_dir, obs_dir)
    assert b == 0.0, f"Expected zero brightness, got {b}"
    print("PASS: Back-illumination gives zero brightness")


if __name__ == '__main__':
    print("=" * 60)
    print("Forward Model Tests")
    print("=" * 60)
    test_kepler_solver()
    test_mesh_properties()
    test_brightness_zero_for_back_illumination()
    test_sphere_constant_brightness()
    test_ellipsoid_amplitude()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
