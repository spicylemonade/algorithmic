"""
Tests for C++ extension (cpp_ext)

Validates:
1. C++ extension compiles and loads
2. Results match Python reference to < 1e-10 relative tolerance
3. Benchmark: >= 10x speedup over pure Python on mesh with >= 1000 facets
   and >= 1000 epochs
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import time
from forward_model import (create_sphere_mesh, create_ellipsoid_mesh,
                           generate_lightcurve_direct, TriMesh,
                           compute_face_properties)
from geometry import SpinState, ecliptic_to_body_matrix

np.random.seed(42)


# -----------------------------------------------------------------------
# Test: extension loads
# -----------------------------------------------------------------------

def test_extension_loads():
    """C++ extension loads successfully."""
    from cpp_ext import generate_lightcurve_direct_cpp
    assert callable(generate_lightcurve_direct_cpp)
    print("PASS: C++ extension loads")


# -----------------------------------------------------------------------
# Test: correctness — matches Python to < 1e-10
# -----------------------------------------------------------------------

def test_correctness_sphere():
    """C++ brightness matches Python for a sphere."""
    from cpp_ext import generate_lightcurve_direct_cpp

    mesh = create_sphere_mesh(n_subdivisions=3)  # 1280 faces
    rng = np.random.default_rng(42)

    n_epochs = 100
    sun_dirs = rng.standard_normal((n_epochs, 3))
    sun_dirs /= np.linalg.norm(sun_dirs, axis=1, keepdims=True)
    obs_dirs = sun_dirs + 0.1 * rng.standard_normal((n_epochs, 3))
    obs_dirs /= np.linalg.norm(obs_dirs, axis=1, keepdims=True)

    for c_lambert in [0.0, 0.1, 0.5, 1.0]:
        py_result = generate_lightcurve_direct(mesh, sun_dirs, obs_dirs, c_lambert)
        cpp_result = generate_lightcurve_direct_cpp(mesh, sun_dirs, obs_dirs, c_lambert)

        # Relative tolerance check
        mask = py_result > 1e-20  # avoid division by near-zero
        if np.sum(mask) > 0:
            rel_err = np.abs(cpp_result[mask] - py_result[mask]) / py_result[mask]
            max_rel_err = np.max(rel_err)
            assert max_rel_err < 1e-10, \
                f"c_lambert={c_lambert}: max rel error {max_rel_err:.2e} >= 1e-10"

        # Absolute check for zero-brightness epochs
        assert np.allclose(cpp_result, py_result, rtol=1e-10, atol=1e-20), \
            f"c_lambert={c_lambert}: results don't match"

    print("PASS: C++ matches Python (sphere, 4 c_lambert values, rtol < 1e-10)")


def test_correctness_ellipsoid():
    """C++ brightness matches Python for an ellipsoid."""
    from cpp_ext import generate_lightcurve_direct_cpp

    mesh = create_ellipsoid_mesh(2.0, 1.0, 0.8, n_subdivisions=3)
    rng = np.random.default_rng(123)

    n_epochs = 200
    sun_dirs = rng.standard_normal((n_epochs, 3))
    sun_dirs /= np.linalg.norm(sun_dirs, axis=1, keepdims=True)
    obs_dirs = rng.standard_normal((n_epochs, 3))
    obs_dirs /= np.linalg.norm(obs_dirs, axis=1, keepdims=True)

    py_result = generate_lightcurve_direct(mesh, sun_dirs, obs_dirs, 0.1)
    cpp_result = generate_lightcurve_direct_cpp(mesh, sun_dirs, obs_dirs, 0.1)

    assert np.allclose(cpp_result, py_result, rtol=1e-10, atol=1e-20), \
        "Ellipsoid results don't match"
    print("PASS: C++ matches Python (ellipsoid)")


# -----------------------------------------------------------------------
# Test: benchmark — >= 10x speedup
# -----------------------------------------------------------------------

def test_benchmark():
    """C++ extension achieves >= 10x speedup over Python.

    Uses >= 1000 facets and >= 1000 data points as required.
    """
    from cpp_ext import generate_lightcurve_direct_cpp

    # Create mesh with >= 1000 faces
    mesh = create_sphere_mesh(n_subdivisions=4)  # 5120 faces
    n_faces = len(mesh.faces)
    assert n_faces >= 1000, f"Mesh has {n_faces} faces, need >= 1000"

    # Generate >= 1000 epochs
    n_epochs = 1000
    rng = np.random.default_rng(42)
    sun_dirs = rng.standard_normal((n_epochs, 3))
    sun_dirs /= np.linalg.norm(sun_dirs, axis=1, keepdims=True)
    obs_dirs = sun_dirs + 0.1 * rng.standard_normal((n_epochs, 3))
    obs_dirs /= np.linalg.norm(obs_dirs, axis=1, keepdims=True)

    c_lambert = 0.1

    # Warmup
    _ = generate_lightcurve_direct(mesh, sun_dirs[:10], obs_dirs[:10], c_lambert)
    _ = generate_lightcurve_direct_cpp(mesh, sun_dirs[:10], obs_dirs[:10], c_lambert)

    # Benchmark Python
    n_repeats = 3
    py_times = []
    for _ in range(n_repeats):
        t0 = time.perf_counter()
        _ = generate_lightcurve_direct(mesh, sun_dirs, obs_dirs, c_lambert)
        py_times.append(time.perf_counter() - t0)
    py_time = min(py_times)

    # Benchmark C++
    cpp_times = []
    for _ in range(n_repeats):
        t0 = time.perf_counter()
        _ = generate_lightcurve_direct_cpp(mesh, sun_dirs, obs_dirs, c_lambert)
        cpp_times.append(time.perf_counter() - t0)
    cpp_time = min(cpp_times)

    speedup = py_time / cpp_time if cpp_time > 0 else float('inf')

    print(f"  Mesh: {n_faces} faces, {n_epochs} epochs")
    print(f"  Python time: {py_time * 1000:.1f} ms")
    print(f"  C++ time:    {cpp_time * 1000:.1f} ms")
    print(f"  Speedup:     {speedup:.1f}x")

    assert speedup >= 10, \
        f"Speedup {speedup:.1f}x is below 10x threshold"
    print(f"PASS: C++ achieves {speedup:.1f}x speedup (>= 10x)")


if __name__ == '__main__':
    print("=" * 60)
    print("C++ Extension Tests")
    print("=" * 60)
    test_extension_loads()
    test_correctness_sphere()
    test_correctness_ellipsoid()
    test_benchmark()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
