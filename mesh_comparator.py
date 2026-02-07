"""
Mesh Comparator (Module 5)

Quantitatively compares two 3D shape models using Hausdorff distance
and Volumetric Intersection over Union (IoU).

References:
    Cignoni et al. (1998) -- Metro: Hausdorff distance for meshes
"""

import numpy as np
from scipy.spatial import KDTree
from forward_model import TriMesh, load_obj


# ---------------------------------------------------------------------------
# Surface sampling
# ---------------------------------------------------------------------------

def sample_surface_points(mesh, n_points=10000):
    """Sample random points uniformly on the surface of a triangle mesh.

    For each sample a random triangle is chosen (weighted by area) and a
    random point inside that triangle is generated via barycentric
    coordinates.

    Parameters
    ----------
    mesh : TriMesh
        Triangulated mesh with ``vertices``, ``faces``, and ``areas``.
    n_points : int
        Number of surface points to sample.

    Returns
    -------
    points : np.ndarray, shape (n_points, 3)
        Sampled 3-D surface points.
    """
    areas = mesh.areas
    # Probability of picking each triangle is proportional to its area
    probs = areas / areas.sum()

    # Choose which triangle each sample belongs to
    tri_indices = np.random.choice(len(areas), size=n_points, p=probs)

    # Random barycentric coordinates for each sample
    r1 = np.random.rand(n_points)
    r2 = np.random.rand(n_points)
    sqrt_r1 = np.sqrt(r1)
    u = 1.0 - sqrt_r1
    v = sqrt_r1 * (1.0 - r2)
    w = sqrt_r1 * r2

    # Vertices of the selected triangles
    v0 = mesh.vertices[mesh.faces[tri_indices, 0]]  # (n_points, 3)
    v1 = mesh.vertices[mesh.faces[tri_indices, 1]]
    v2 = mesh.vertices[mesh.faces[tri_indices, 2]]

    points = u[:, None] * v0 + v[:, None] * v1 + w[:, None] * v2
    return points


# ---------------------------------------------------------------------------
# Hausdorff distance
# ---------------------------------------------------------------------------

def hausdorff_distance(points_a, points_b):
    """One-sided Hausdorff distance from *points_a* to *points_b*.

    For every point in A find the nearest neighbour in B, then return the
    maximum of those distances:

        h(A, B) = max_{a in A}  min_{b in B}  ||a - b||

    Uses ``scipy.spatial.KDTree`` for efficient nearest-neighbour queries.

    Parameters
    ----------
    points_a : np.ndarray, shape (N, 3)
    points_b : np.ndarray, shape (M, 3)

    Returns
    -------
    float
        One-sided Hausdorff distance h(A, B).
    """
    tree_b = KDTree(points_b)
    distances, _ = tree_b.query(points_a)
    return float(np.max(distances))


def symmetric_hausdorff(points_a, points_b):
    """Symmetric Hausdorff distance.

        H(A, B) = max( h(A, B), h(B, A) )

    Parameters
    ----------
    points_a : np.ndarray, shape (N, 3)
    points_b : np.ndarray, shape (M, 3)

    Returns
    -------
    float
        Symmetric Hausdorff distance.
    """
    return max(hausdorff_distance(points_a, points_b),
               hausdorff_distance(points_b, points_a))


def chamfer_distance(points_a, points_b):
    """Chamfer distance between two point clouds.

    The Chamfer distance is the mean of average nearest-neighbour distances
    in both directions:

        CD = (1/|A|) sum_{a} min_b ||a-b|| + (1/|B|) sum_{b} min_a ||b-a||

    Parameters
    ----------
    points_a : np.ndarray, shape (N, 3)
    points_b : np.ndarray, shape (M, 3)

    Returns
    -------
    float
        Chamfer distance.
    """
    tree_b = KDTree(points_b)
    tree_a = KDTree(points_a)
    dist_a_to_b, _ = tree_b.query(points_a)
    dist_b_to_a, _ = tree_a.query(points_b)
    return float(np.mean(dist_a_to_b) + np.mean(dist_b_to_a))


# ---------------------------------------------------------------------------
# Voxelisation helpers
# ---------------------------------------------------------------------------

def _ray_mesh_intersections_z(grid_xy, mesh):
    """Count intersections of +z rays with mesh triangles for each grid point.

    For every (x, y) position in *grid_xy* a ray is cast along the +z
    direction.  The number of intersections with each triangle of the mesh
    is accumulated using the Moeller--Trumbore-style slab test projected
    onto the xy-plane.

    Parameters
    ----------
    grid_xy : np.ndarray, shape (P, 2)
        x, y coordinates of grid points.
    mesh : TriMesh
        Triangle mesh.

    Returns
    -------
    counts : np.ndarray, shape (P,)
        Number of triangle intersections for each grid point.
    """
    v0 = mesh.vertices[mesh.faces[:, 0]]  # (F, 3)
    v1 = mesh.vertices[mesh.faces[:, 1]]
    v2 = mesh.vertices[mesh.faces[:, 2]]

    counts = np.zeros(len(grid_xy), dtype=np.int64)

    for fi in range(len(mesh.faces)):
        a = v0[fi]
        b = v1[fi]
        c = v2[fi]

        # Edges in xy
        ab = b[:2] - a[:2]
        ac = c[:2] - a[:2]

        det = ab[0] * ac[1] - ab[1] * ac[0]
        if abs(det) < 1e-30:
            continue  # degenerate triangle in xy projection

        inv_det = 1.0 / det

        # Vector from triangle vertex a to each grid point (xy only)
        ap = grid_xy - a[:2]  # (P, 2)

        # Barycentric coords in xy
        u = (ap[:, 0] * ac[1] - ap[:, 1] * ac[0]) * inv_det
        v = (ab[0] * ap[:, 1] - ab[1] * ap[:, 0]) * inv_det

        # Inside triangle? (u >= 0, v >= 0, u + v <= 1)
        inside = (u >= 0) & (v >= 0) & (u + v <= 1.0)

        # Compute z of intersection for those points
        z_hit = a[2] + u * (b[2] - a[2]) + v * (c[2] - a[2])

        # We only want intersections *above* the grid z -- but we will
        # handle the full column in the caller, so just count all hits.
        # Actually, we test a specific z later. For now count all.
        counts[inside] += 1

    return counts


def voxelize_mesh(mesh, resolution=64, bbox_min=None, bbox_max=None):
    """Voxelize a mesh into a 3-D boolean occupancy grid.

    A ray is cast in the +z direction from each (x, y) column of the grid.
    Intersections with the mesh surface are computed, and for each voxel
    centre the parity of intersections *below* that z value determines
    inside/outside (odd = inside).

    Parameters
    ----------
    mesh : TriMesh
        Triangle mesh.
    resolution : int
        Number of voxels along each axis.
    bbox_min : np.ndarray, shape (3,), optional
        Minimum corner of bounding box.  Computed from mesh if *None*.
    bbox_max : np.ndarray, shape (3,), optional
        Maximum corner of bounding box.  Computed from mesh if *None*.

    Returns
    -------
    voxels : np.ndarray, shape (resolution, resolution, resolution), dtype bool
        Occupancy grid (*True* = inside mesh).
    bbox_min : np.ndarray, shape (3,)
    bbox_max : np.ndarray, shape (3,)
    """
    needs_padding = bbox_min is None or bbox_max is None
    if bbox_min is None:
        bbox_min = mesh.vertices.min(axis=0)
    if bbox_max is None:
        bbox_max = mesh.vertices.max(axis=0)

    if needs_padding:
        # Small padding so that surface voxels are not right on the boundary
        pad = (bbox_max - bbox_min) * 0.02
        bbox_min = bbox_min - pad
        bbox_max = bbox_max + pad

    # Voxel centres
    xs = np.linspace(bbox_min[0], bbox_max[0], resolution)
    ys = np.linspace(bbox_min[1], bbox_max[1], resolution)
    zs = np.linspace(bbox_min[2], bbox_max[2], resolution)

    voxels = np.zeros((resolution, resolution, resolution), dtype=bool)

    v0 = mesh.vertices[mesh.faces[:, 0]]  # (F, 3)
    v1 = mesh.vertices[mesh.faces[:, 1]]
    v2 = mesh.vertices[mesh.faces[:, 2]]

    # For each xy column cast a ray in +z and collect all intersection z values
    for ix in range(resolution):
        x = xs[ix]
        for iy in range(resolution):
            y = ys[iy]
            z_hits = _ray_z_hits_for_point(x, y, v0, v1, v2)
            if len(z_hits) == 0:
                continue
            z_hits.sort()
            # For each voxel z-centre, count how many hits are below it
            for iz in range(resolution):
                z = zs[iz]
                n_below = np.searchsorted(z_hits, z)
                if n_below % 2 == 1:
                    voxels[ix, iy, iz] = True

    return voxels, bbox_min, bbox_max


def _ray_z_hits_for_point(px, py, v0, v1, v2):
    """Return z-values of ray-triangle intersections for a single (px, py) ray.

    Parameters
    ----------
    px, py : float
        x, y of the ray origin (ray goes in +z).
    v0, v1, v2 : np.ndarray, shape (F, 3)
        Triangle vertex arrays.

    Returns
    -------
    z_hits : np.ndarray
        z-coordinates of intersection points.
    """
    # Edges in xy
    ab = v1[:, :2] - v0[:, :2]  # (F, 2)
    ac = v2[:, :2] - v0[:, :2]

    det = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]  # (F,)
    non_degenerate = np.abs(det) > 1e-30
    inv_det = np.zeros_like(det)
    inv_det[non_degenerate] = 1.0 / det[non_degenerate]

    # Vector from v0 to point in xy
    ap_x = px - v0[:, 0]
    ap_y = py - v0[:, 1]

    u = (ap_x * ac[:, 1] - ap_y * ac[:, 0]) * inv_det
    v = (ab[:, 0] * ap_y - ab[:, 1] * ap_x) * inv_det

    inside = non_degenerate & (u >= 0) & (v >= 0) & (u + v <= 1.0)

    # z of intersection
    z_hit = v0[inside, 2] + u[inside] * (v1[inside, 2] - v0[inside, 2]) + v[inside] * (v2[inside, 2] - v0[inside, 2])
    return z_hit


# ---------------------------------------------------------------------------
# Volumetric IoU
# ---------------------------------------------------------------------------

def volumetric_iou(voxels_a, voxels_b):
    """Intersection over Union of two boolean voxel grids.

    Parameters
    ----------
    voxels_a : np.ndarray, dtype bool
    voxels_b : np.ndarray, dtype bool

    Returns
    -------
    float
        IoU in [0, 1].
    """
    intersection = np.sum(voxels_a & voxels_b)
    union = np.sum(voxels_a | voxels_b)
    if union == 0:
        return 1.0  # both empty
    return float(intersection) / float(union)


# ---------------------------------------------------------------------------
# Normalized Hausdorff
# ---------------------------------------------------------------------------

def normalized_hausdorff(hausdorff_dist, mesh):
    """Hausdorff distance as a fraction of the mesh bounding-box diagonal.

    Parameters
    ----------
    hausdorff_dist : float
        Hausdorff distance value.
    mesh : TriMesh
        Mesh used as reference for normalisation.

    Returns
    -------
    float
        Normalised Hausdorff distance in [0, 1+].
    """
    bbox_min = mesh.vertices.min(axis=0)
    bbox_max = mesh.vertices.max(axis=0)
    diagonal = float(np.linalg.norm(bbox_max - bbox_min))
    if diagonal < 1e-30:
        return 0.0
    return hausdorff_dist / diagonal


# ---------------------------------------------------------------------------
# Full comparison
# ---------------------------------------------------------------------------

def compare_meshes(mesh_a, mesh_b, n_surface_points=10000, voxel_resolution=64):
    """Run a full quantitative comparison between two meshes.

    Parameters
    ----------
    mesh_a : TriMesh
        First mesh (reference).
    mesh_b : TriMesh
        Second mesh (test).
    n_surface_points : int
        Number of surface sample points per mesh.
    voxel_resolution : int
        Voxel grid resolution.

    Returns
    -------
    dict
        Keys:
        - ``hausdorff_ab`` : one-sided Hausdorff A -> B
        - ``hausdorff_ba`` : one-sided Hausdorff B -> A
        - ``hausdorff_symmetric`` : symmetric Hausdorff
        - ``chamfer_distance`` : Chamfer distance
        - ``iou`` : Volumetric Intersection over Union
    """
    pts_a = sample_surface_points(mesh_a, n_surface_points)
    pts_b = sample_surface_points(mesh_b, n_surface_points)

    h_ab = hausdorff_distance(pts_a, pts_b)
    h_ba = hausdorff_distance(pts_b, pts_a)
    h_sym = max(h_ab, h_ba)
    cd = chamfer_distance(pts_a, pts_b)

    # Shared bounding box for voxelisation
    all_verts = np.vstack([mesh_a.vertices, mesh_b.vertices])
    bbox_min = all_verts.min(axis=0)
    bbox_max = all_verts.max(axis=0)

    vox_a, _, _ = voxelize_mesh(mesh_a, voxel_resolution, bbox_min.copy(), bbox_max.copy())
    vox_b, _, _ = voxelize_mesh(mesh_b, voxel_resolution, bbox_min.copy(), bbox_max.copy())
    iou = volumetric_iou(vox_a, vox_b)

    return {
        'hausdorff_ab': h_ab,
        'hausdorff_ba': h_ba,
        'hausdorff_symmetric': h_sym,
        'chamfer_distance': cd,
        'iou': iou,
    }
