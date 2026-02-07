"""
Tests for mesh_comparator.py

Validates:
1. Identical meshes: Hausdorff = 0, IoU = 1.0
2. Sphere vs sphere scaled by 1.1x: analytically verifiable results within 5%
   - Expected Hausdorff ~ 0.1 (unit sphere vs 1.1-radius sphere)
   - Expected IoU ~ (1.0)^3 / (1.1)^3 = 0.751 (ratio of volumes)
3. Normalized Hausdorff correctness
4. Chamfer distance consistency
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from forward_model import (create_sphere_mesh, create_ellipsoid_mesh,
                           TriMesh, compute_face_properties)
from mesh_comparator import (
    sample_surface_points,
    hausdorff_distance,
    symmetric_hausdorff,
    chamfer_distance,
    voxelize_mesh,
    volumetric_iou,
    compare_meshes,
    normalized_hausdorff,
)

np.random.seed(42)


def _make_scaled_sphere(scale, n_subdivisions=3):
    """Create a sphere mesh with the given radius *scale*."""
    sphere = create_sphere_mesh(n_subdivisions=n_subdivisions)
    vertices = sphere.vertices * scale
    normals, areas = compute_face_properties(vertices, sphere.faces)
    return TriMesh(vertices=vertices, faces=sphere.faces,
                   normals=normals, areas=areas)


# -----------------------------------------------------------------------
# Test: surface sampling
# -----------------------------------------------------------------------

def test_sample_surface_points_count():
    """Sampled point cloud has the requested number of points."""
    sphere = create_sphere_mesh(n_subdivisions=2)
    pts = sample_surface_points(sphere, n_points=5000)
    assert pts.shape == (5000, 3), f"Expected (5000, 3), got {pts.shape}"
    print("PASS: sample_surface_points returns correct shape")


def test_sample_surface_points_on_sphere():
    """Points sampled from a unit sphere should lie near the surface (r ~ 1)."""
    np.random.seed(42)
    sphere = create_sphere_mesh(n_subdivisions=3)
    pts = sample_surface_points(sphere, n_points=10000)
    radii = np.linalg.norm(pts, axis=1)
    # All radii should be very close to 1.0 for a unit icosphere
    assert np.allclose(radii, 1.0, atol=0.05), \
        f"Radii range [{radii.min():.4f}, {radii.max():.4f}], expected ~1.0"
    print("PASS: sampled points lie on sphere surface")


# -----------------------------------------------------------------------
# Test: identical meshes
# -----------------------------------------------------------------------

def test_identical_meshes_hausdorff_zero():
    """Hausdorff distance between a mesh and itself should be ~0."""
    np.random.seed(42)
    sphere = create_sphere_mesh(n_subdivisions=3)
    pts = sample_surface_points(sphere, n_points=10000)
    h = symmetric_hausdorff(pts, pts)
    assert h < 1e-12, f"Expected ~0 Hausdorff for identical points, got {h}"
    print("PASS: identical meshes have Hausdorff ~ 0")


def test_identical_meshes_iou_one():
    """Volumetric IoU of a mesh with itself should be 1.0."""
    np.random.seed(42)
    sphere = create_sphere_mesh(n_subdivisions=3)
    vox, _, _ = voxelize_mesh(sphere, resolution=32)
    iou = volumetric_iou(vox, vox)
    assert iou == 1.0, f"Expected IoU = 1.0, got {iou}"
    print("PASS: identical voxels have IoU = 1.0")


# -----------------------------------------------------------------------
# Test: unit sphere vs 1.1x sphere
# -----------------------------------------------------------------------

def test_sphere_vs_scaled_hausdorff():
    """Hausdorff between unit sphere and 1.1x sphere should be ~ 0.1.

    The *true* surface Hausdorff is exactly 0.1.  Because we approximate
    surfaces by finite point samples the sampled Hausdorff is a biased
    *overestimate* (each max-of-min value >= true distance).  We therefore
    verify that:
        0.1  <=  H_sampled  <=  0.1 * 1.05   (within 5% above)
    """
    np.random.seed(42)
    sphere_1 = create_sphere_mesh(n_subdivisions=4)
    sphere_11 = _make_scaled_sphere(1.1, n_subdivisions=4)

    # Use mesh vertices (exact sphere points) plus dense random samples
    pts_1 = np.vstack([sphere_1.vertices,
                        sample_surface_points(sphere_1, n_points=100000)])
    pts_11 = np.vstack([sphere_11.vertices,
                         sample_surface_points(sphere_11, n_points=100000)])

    h_sym = symmetric_hausdorff(pts_1, pts_11)
    expected = 0.1

    print(f"  Symmetric Hausdorff: {h_sym:.4f}")
    print(f"  Expected:            {expected:.4f}")

    # The sampled value must be at least the true value (it is an overestimate)
    assert h_sym >= expected * 0.99, \
        f"Hausdorff {h_sym:.4f} unexpectedly below true value {expected}"
    # And within 5% above the true value
    assert h_sym <= expected * 1.05, \
        f"Hausdorff {h_sym:.4f} exceeds 5% above true value {expected}"
    print("PASS: sphere vs 1.1x sphere Hausdorff within 5%")


def test_sphere_vs_scaled_iou():
    """IoU between unit sphere and 1.1x sphere ~ 1/1.1^3 = 0.751."""
    np.random.seed(42)
    sphere_1 = create_sphere_mesh(n_subdivisions=3)
    sphere_11 = _make_scaled_sphere(1.1, n_subdivisions=3)

    # Use a decent resolution; 48 gives good accuracy
    vox_1, bmin, bmax = voxelize_mesh(sphere_11, resolution=48)
    # Re-voxelize with matching bounding box
    vox_small, _, _ = voxelize_mesh(sphere_1, resolution=48,
                                    bbox_min=bmin.copy(),
                                    bbox_max=bmax.copy())

    iou = volumetric_iou(vox_small, vox_1)
    # The smaller sphere is entirely inside the larger one, so
    #   intersection = volume(small), union = volume(large)
    #   IoU = V_small / V_large = (1.0/1.1)^3 ~ 0.7513
    expected_iou = (1.0 / 1.1) ** 3
    error_pct = abs(iou - expected_iou) / expected_iou * 100

    print(f"  Volumetric IoU: {iou:.4f}")
    print(f"  Expected IoU:   {expected_iou:.4f}")
    print(f"  Error:          {error_pct:.2f}%")

    assert error_pct < 5.0, \
        f"IoU error {error_pct:.2f}% exceeds 5% tolerance"
    print("PASS: sphere vs 1.1x sphere IoU within 5%")


# -----------------------------------------------------------------------
# Test: compare_meshes integration
# -----------------------------------------------------------------------

def test_compare_meshes_returns_all_keys():
    """compare_meshes should return dict with all expected keys."""
    np.random.seed(42)
    sphere = create_sphere_mesh(n_subdivisions=2)
    result = compare_meshes(sphere, sphere,
                            n_surface_points=1000, voxel_resolution=16)
    expected_keys = {'hausdorff_ab', 'hausdorff_ba', 'hausdorff_symmetric',
                     'chamfer_distance', 'iou'}
    assert set(result.keys()) == expected_keys, \
        f"Keys mismatch: {set(result.keys())} vs {expected_keys}"
    print("PASS: compare_meshes returns all expected keys")


# -----------------------------------------------------------------------
# Test: normalized Hausdorff
# -----------------------------------------------------------------------

def test_normalized_hausdorff():
    """Normalized Hausdorff should equal raw / bbox diagonal."""
    np.random.seed(42)
    sphere = create_sphere_mesh(n_subdivisions=3)
    # Bounding box diagonal of unit icosphere is 2.0 (from -1 to +1 along
    # each axis, diagonal = sqrt(3)*2 ~ 3.46 -- but actual icosphere vertices
    # are exactly on the unit sphere so diagonal = 2*sqrt(3) ... let's just
    # compute it)
    bbox_diag = float(np.linalg.norm(sphere.vertices.max(axis=0) -
                                      sphere.vertices.min(axis=0)))

    raw_h = 0.25  # arbitrary
    nh = normalized_hausdorff(raw_h, sphere)
    expected = raw_h / bbox_diag
    assert abs(nh - expected) < 1e-12, \
        f"normalized_hausdorff mismatch: {nh} vs {expected}"
    print("PASS: normalized_hausdorff")


# -----------------------------------------------------------------------
# Test: chamfer distance
# -----------------------------------------------------------------------

def test_chamfer_distance_identical_zero():
    """Chamfer distance of identical point clouds should be 0."""
    np.random.seed(42)
    pts = np.random.rand(500, 3)
    cd = chamfer_distance(pts, pts)
    assert cd < 1e-12, f"Expected ~0 Chamfer distance, got {cd}"
    print("PASS: chamfer distance for identical points ~ 0")


def test_chamfer_distance_positive():
    """Chamfer distance should be > 0 for distinct point clouds."""
    np.random.seed(42)
    sphere_1 = create_sphere_mesh(n_subdivisions=3)
    sphere_11 = _make_scaled_sphere(1.1, n_subdivisions=3)
    pts_1 = sample_surface_points(sphere_1, n_points=5000)
    pts_11 = sample_surface_points(sphere_11, n_points=5000)
    cd = chamfer_distance(pts_1, pts_11)
    assert cd > 0, f"Expected positive Chamfer distance, got {cd}"
    print(f"PASS: chamfer distance positive ({cd:.4f})")


# -----------------------------------------------------------------------
# Test: voxelization sanity
# -----------------------------------------------------------------------

def test_voxelize_sphere_volume():
    """Voxelized unit sphere volume should be close to 4/3 pi."""
    np.random.seed(42)
    sphere = create_sphere_mesh(n_subdivisions=3)
    res = 48
    vox, bmin, bmax = voxelize_mesh(sphere, resolution=res)
    voxel_size = (bmax - bmin) / res
    voxel_volume = voxel_size[0] * voxel_size[1] * voxel_size[2]
    total_volume = float(np.sum(vox)) * voxel_volume
    expected = 4.0 / 3.0 * np.pi  # ~4.189 for unit sphere
    error_pct = abs(total_volume - expected) / expected * 100

    print(f"  Voxelized volume: {total_volume:.4f}")
    print(f"  Analytic volume:  {expected:.4f}")
    print(f"  Error:            {error_pct:.2f}%")

    assert error_pct < 10.0, \
        f"Voxelized sphere volume error {error_pct:.2f}% exceeds 10%"
    print("PASS: voxelized unit sphere volume within 10%")


if __name__ == '__main__':
    print("=" * 60)
    print("Mesh Comparator Tests")
    print("=" * 60)
    test_sample_surface_points_count()
    test_sample_surface_points_on_sphere()
    test_identical_meshes_hausdorff_zero()
    test_identical_meshes_iou_one()
    test_sphere_vs_scaled_hausdorff()
    test_sphere_vs_scaled_iou()
    test_compare_meshes_returns_all_keys()
    test_normalized_hausdorff()
    test_chamfer_distance_identical_zero()
    test_chamfer_distance_positive()
    test_voxelize_sphere_volume()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
