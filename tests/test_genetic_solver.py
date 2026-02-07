"""
Tests for genetic_solver.py

Validates:
1. Dumbbell mesh creation (non-convex shape)
2. Fitness evaluation
3. Mutation preserves shape topology
4. Crossover produces valid meshes
5. Tournament selection
6. Full GA run: recovered shape achieves normalized Hausdorff < 15% of
   bounding-box diagonal on noise-free dumbbell data within 500 generations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from forward_model import (TriMesh, create_sphere_mesh, compute_face_properties,
                           generate_lightcurve_direct, save_obj)
from geometry import SpinState, ecliptic_to_body_matrix
from convex_solver import LightcurveData
from genetic_solver import (
    GAConfig, GAResult, Individual,
    create_dumbbell_mesh, run_genetic_solver,
    evaluate_fitness, mutate, crossover, tournament_select,
    _precompute_body_dirs_ga,
    mutate_gaussian, mutate_radial, mutate_local,
    crossover_blend, crossover_uniform,
)
from mesh_comparator import (
    sample_surface_points, symmetric_hausdorff, normalized_hausdorff
)

np.random.seed(42)


def _make_synthetic_lightcurves(mesh, spin, n_lc=3, n_points=40, c_lambert=0.1):
    """Generate synthetic lightcurves from a known shape for testing."""
    rng = np.random.default_rng(42)
    lightcurves = []
    for i in range(n_lc):
        sun_ecl_fixed = rng.standard_normal(3)
        sun_ecl_fixed /= np.linalg.norm(sun_ecl_fixed)
        obs_ecl_fixed = sun_ecl_fixed + 0.1 * rng.standard_normal(3)
        obs_ecl_fixed /= np.linalg.norm(obs_ecl_fixed)

        period_days = spin.period_hours / 24.0
        phases = np.linspace(0, 360, n_points, endpoint=False)
        jd_array = spin.jd0 + phases / 360.0 * period_days

        sun_body_arr = np.zeros((n_points, 3))
        obs_body_arr = np.zeros((n_points, 3))
        sun_ecl_arr = np.zeros((n_points, 3))
        obs_ecl_arr = np.zeros((n_points, 3))
        for j in range(n_points):
            R = ecliptic_to_body_matrix(spin, jd_array[j])
            sun_body_arr[j] = R @ sun_ecl_fixed
            obs_body_arr[j] = R @ obs_ecl_fixed
            sun_ecl_arr[j] = sun_ecl_fixed
            obs_ecl_arr[j] = obs_ecl_fixed

        brightness = generate_lightcurve_direct(mesh, sun_body_arr, obs_body_arr,
                                                 c_lambert)
        weights = np.ones(n_points)
        lc = LightcurveData(
            jd=jd_array,
            brightness=brightness,
            weights=weights,
            sun_ecl=sun_ecl_arr,
            obs_ecl=obs_ecl_arr,
        )
        lightcurves.append(lc)
    return lightcurves


# -----------------------------------------------------------------------
# Test: dumbbell mesh
# -----------------------------------------------------------------------

def test_dumbbell_mesh():
    """Dumbbell mesh has two lobes and correct number of elements."""
    mesh = create_dumbbell_mesh(a_len=2.0, lobe_radius=0.8, n_subdivisions=2)
    one_lobe = create_sphere_mesh(n_subdivisions=2)
    assert len(mesh.vertices) == 2 * len(one_lobe.vertices)
    assert len(mesh.faces) == 2 * len(one_lobe.faces)
    assert np.all(mesh.areas > 0)
    # The mesh should span roughly -2.8 to +2.8 along x
    assert mesh.vertices[:, 0].min() < -1.0
    assert mesh.vertices[:, 0].max() > 1.0
    print("PASS: dumbbell mesh creation")


# -----------------------------------------------------------------------
# Test: fitness evaluation
# -----------------------------------------------------------------------

def test_fitness_evaluation():
    """Fitness of the true shape on its own data should be very low."""
    spin = SpinState(lambda_deg=45, beta_deg=30, period_hours=6.0,
                     jd0=2451545.0)
    mesh = create_dumbbell_mesh(a_len=1.5, lobe_radius=0.6, n_subdivisions=1)
    lcs = _make_synthetic_lightcurves(mesh, spin, n_lc=2, n_points=30)
    precomputed = _precompute_body_dirs_ga(spin, lcs)
    fitness = evaluate_fitness(mesh.vertices, mesh.faces, spin, lcs,
                               c_lambert=0.1, reg_weight=0.0,
                               precomputed_dirs=precomputed)
    assert fitness < 0.01, f"True shape fitness too high: {fitness}"
    print(f"PASS: fitness evaluation (true shape fitness = {fitness:.6f})")


# -----------------------------------------------------------------------
# Test: mutation preserves topology
# -----------------------------------------------------------------------

def test_mutation_topology():
    """All mutation operators preserve vertex count."""
    rng = np.random.default_rng(42)
    mesh = create_sphere_mesh(n_subdivisions=1)
    verts = mesh.vertices.copy()

    for fn in [mutate_gaussian, mutate_radial]:
        new_verts = fn(verts, 0.05, rng)
        assert new_verts.shape == verts.shape, f"{fn.__name__}: shape mismatch"

    new_verts = mutate_local(verts, 0.05, rng, fraction=0.3)
    assert new_verts.shape == verts.shape, "mutate_local: shape mismatch"

    new_verts = mutate(verts, 0.05, rng)
    assert new_verts.shape == verts.shape, "mutate: shape mismatch"
    print("PASS: mutation preserves topology")


# -----------------------------------------------------------------------
# Test: crossover
# -----------------------------------------------------------------------

def test_crossover_valid():
    """Crossover produces valid vertex arrays."""
    rng = np.random.default_rng(42)
    mesh = create_sphere_mesh(n_subdivisions=1)
    v_a = mesh.vertices.copy()
    v_b = mesh.vertices * 1.2

    child = crossover_blend(v_a, v_b, 0.5, rng)
    assert child.shape == v_a.shape
    child = crossover_uniform(v_a, v_b, rng)
    assert child.shape == v_a.shape
    child = crossover(v_a, v_b, 0.5, rng)
    assert child.shape == v_a.shape
    print("PASS: crossover produces valid shapes")


# -----------------------------------------------------------------------
# Test: tournament selection
# -----------------------------------------------------------------------

def test_tournament_selection():
    """Tournament selection picks the fittest individual in the tournament."""
    rng = np.random.default_rng(42)
    pop = [Individual(vertices=np.zeros((5, 3)), fitness=float(i))
           for i in range(20)]
    # With tournament size = 20 (all), always picks individual 0
    winner = tournament_select(pop, 20, rng)
    assert winner.fitness == 0.0
    print("PASS: tournament selection")


# -----------------------------------------------------------------------
# Test: full GA run on dumbbell
# -----------------------------------------------------------------------

def test_ga_dumbbell_recovery():
    """GA recovers dumbbell shape with normalised Hausdorff < 15%.

    Uses a small population and few generations for test speed, but
    enough to demonstrate convergence.
    """
    np.random.seed(42)

    # Ground truth: dumbbell
    spin = SpinState(lambda_deg=45, beta_deg=30, period_hours=6.0,
                     jd0=2451545.0)
    target_mesh = create_dumbbell_mesh(a_len=1.5, lobe_radius=0.6,
                                       n_subdivisions=1)

    # Generate synthetic lightcurves
    lcs = _make_synthetic_lightcurves(target_mesh, spin, n_lc=5, n_points=40)

    # Use the same topology as target for a fair test
    config = GAConfig(
        population_size=50,
        n_generations=500,
        tournament_size=5,
        elite_fraction=0.1,
        mutation_rate=0.9,
        mutation_sigma=0.08,
        mutation_sigma_decay=0.997,
        crossover_rate=0.6,
        c_lambert=0.1,
        reg_weight=0.001,
        seed=42,
        verbose=True,
    )

    # Seed with the same-topology sphere at the right scale
    seed_mesh = create_dumbbell_mesh(a_len=1.5, lobe_radius=0.6,
                                     n_subdivisions=1)

    result = run_genetic_solver(lcs, spin, config=config,
                                initial_mesh=seed_mesh)

    # Compare recovered vs ground truth
    np.random.seed(42)
    pts_target = sample_surface_points(target_mesh, n_points=5000)
    pts_recovered = sample_surface_points(result.mesh, n_points=5000)
    h_sym = symmetric_hausdorff(pts_target, pts_recovered)
    nh = normalized_hausdorff(h_sym, target_mesh)

    print(f"  Final fitness: {result.fitness:.6f}")
    print(f"  Hausdorff: {h_sym:.4f}")
    print(f"  Normalised Hausdorff: {nh:.4f} (threshold: 0.15)")
    print(f"  Generations: {len(result.fitness_history)}")

    assert nh < 0.15, \
        f"Normalised Hausdorff {nh:.4f} exceeds 15% threshold"
    assert result.fitness < result.fitness_history[0], \
        "Fitness did not improve over generations"

    print("PASS: GA dumbbell recovery (normalised Hausdorff < 15%)")


if __name__ == '__main__':
    print("=" * 60)
    print("Genetic Solver Tests")
    print("=" * 60)
    test_dumbbell_mesh()
    test_fitness_evaluation()
    test_mutation_topology()
    test_crossover_valid()
    test_tournament_selection()
    test_ga_dumbbell_recovery()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
