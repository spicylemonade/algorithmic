"""
Evolutionary / Genetic Algorithm Solver for Non-Convex Shapes (Module 3)

Population-based optimizer where individuals are triangulated meshes with
vertex-based representation.  Implements mutation, crossover, tournament
selection, and a lightcurve chi-squared fitness function.

Inspired by the SAGE approach (Bartczak & Dudzinski 2018) which evolves
vertex-based non-convex shape models.

References:
    Bartczak & Dudzinski (2018) — SAGE genetic algorithm
    Cellino et al. (2009) — evolutionary shape modeling
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from forward_model import (TriMesh, create_sphere_mesh, create_ellipsoid_mesh,
                           compute_face_properties, generate_lightcurve_direct,
                           save_obj)
from geometry import SpinState, ecliptic_to_body_matrix
from convex_solver import LightcurveData


@dataclass
class Individual:
    """One member of the population — a vertex-displaced mesh."""
    vertices: np.ndarray   # (N_v, 3) mutable vertex positions
    fitness: float = np.inf


@dataclass
class GAConfig:
    """Configuration for the genetic algorithm."""
    population_size: int = 50
    n_generations: int = 500
    tournament_size: int = 5
    elite_fraction: float = 0.1
    mutation_rate: float = 0.8
    mutation_sigma: float = 0.05
    mutation_sigma_decay: float = 0.998
    crossover_rate: float = 0.5
    blend_alpha: float = 0.5
    c_lambert: float = 0.1
    reg_weight: float = 0.001
    seed: int = 42
    verbose: bool = False


@dataclass
class GAResult:
    """Result of the genetic algorithm."""
    mesh: TriMesh
    spin: SpinState
    fitness: float
    fitness_history: List[float] = field(default_factory=list)
    generation_best: List[float] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Fitness evaluation
# ---------------------------------------------------------------------------

def _precompute_body_dirs_ga(spin, lightcurves):
    """Pre-compute Sun/observer body-frame directions for all lightcurves."""
    all_dirs = []
    for lc in lightcurves:
        N = len(lc.jd)
        sun_body = np.zeros((N, 3))
        obs_body = np.zeros((N, 3))
        for j in range(N):
            R = ecliptic_to_body_matrix(spin, lc.jd[j])
            sun_body[j] = R @ lc.sun_ecl[j]
            obs_body[j] = R @ lc.obs_ecl[j]
        all_dirs.append((sun_body, obs_body))
    return all_dirs


def evaluate_fitness(vertices, faces, spin, lightcurves, c_lambert=0.1,
                     reg_weight=0.001, precomputed_dirs=None):
    """Compute fitness = lightcurve chi-squared + regularization.

    Parameters
    ----------
    vertices : np.ndarray, shape (N_v, 3)
    faces : np.ndarray, shape (N_f, 3)
    spin : SpinState
    lightcurves : list of LightcurveData
    c_lambert : float
    reg_weight : float
    precomputed_dirs : list of (sun_body, obs_body) tuples

    Returns
    -------
    float
        Fitness value (lower is better).
    """
    normals, areas = compute_face_properties(vertices, faces)
    if np.any(areas <= 0):
        return 1e20
    mesh = TriMesh(vertices=vertices, faces=faces, normals=normals, areas=areas)

    chi2 = 0.0
    n_total = 0
    for idx, lc in enumerate(lightcurves):
        if precomputed_dirs is not None:
            sun_body, obs_body = precomputed_dirs[idx]
        else:
            N = len(lc.jd)
            sun_body = np.zeros((N, 3))
            obs_body = np.zeros((N, 3))
            for j in range(N):
                R = ecliptic_to_body_matrix(spin, lc.jd[j])
                sun_body[j] = R @ lc.sun_ecl[j]
                obs_body[j] = R @ lc.obs_ecl[j]

        model = generate_lightcurve_direct(mesh, sun_body, obs_body, c_lambert)
        if np.all(model == 0):
            chi2 += 1e10
            continue

        w = lc.weights
        c_fit = np.sum(w * lc.brightness * model) / (np.sum(w * model**2) + 1e-30)
        residuals = lc.brightness - c_fit * model
        chi2 += np.sum(w * residuals**2)
        n_total += len(lc.jd)

    if n_total > 0:
        chi2 /= n_total

    # Regularisation: penalise deviation of edge lengths from their initial mean
    if reg_weight > 0:
        edge_vecs = []
        for fi in range(len(faces)):
            for ei in range(3):
                v_a = vertices[faces[fi, ei]]
                v_b = vertices[faces[fi, (ei + 1) % 3]]
                edge_vecs.append(v_a - v_b)
        edge_vecs = np.array(edge_vecs)
        edge_lens = np.linalg.norm(edge_vecs, axis=1)
        mean_edge = np.mean(edge_lens)
        reg = reg_weight * np.sum((edge_lens - mean_edge) ** 2) / (mean_edge ** 2 + 1e-30)
        chi2 += reg

    return chi2


# ---------------------------------------------------------------------------
# Mutation operators
# ---------------------------------------------------------------------------

def mutate_gaussian(vertices, sigma, rng):
    """Perturb each vertex by isotropic Gaussian noise.

    Preserves mesh topology (only positions change).
    """
    new_verts = vertices + rng.normal(0, sigma, vertices.shape)
    return new_verts


def mutate_radial(vertices, sigma, rng):
    """Perturb vertices along radial direction from centroid.

    More physically motivated: models overall shape inflation/deflation.
    """
    centroid = vertices.mean(axis=0)
    dirs = vertices - centroid
    norms = np.linalg.norm(dirs, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-30)
    unit_dirs = dirs / norms
    perturbation = rng.normal(0, sigma, (len(vertices), 1))
    new_verts = vertices + perturbation * unit_dirs
    return new_verts


def mutate_local(vertices, sigma, rng, fraction=0.2):
    """Perturb a random subset of vertices.

    Useful for fine-scale shape features.
    """
    n = len(vertices)
    k = max(1, int(n * fraction))
    indices = rng.choice(n, k, replace=False)
    new_verts = vertices.copy()
    new_verts[indices] += rng.normal(0, sigma, (k, 3))
    return new_verts


def mutate(vertices, sigma, rng):
    """Apply a randomly chosen mutation operator."""
    r = rng.random()
    if r < 0.4:
        return mutate_gaussian(vertices, sigma, rng)
    elif r < 0.7:
        return mutate_radial(vertices, sigma, rng)
    else:
        return mutate_local(vertices, sigma, rng)


# ---------------------------------------------------------------------------
# Crossover operators
# ---------------------------------------------------------------------------

def crossover_blend(parent_a, parent_b, alpha, rng):
    """BLX-alpha blend crossover: each vertex is interpolated between parents.

    Parameters
    ----------
    parent_a, parent_b : np.ndarray, shape (N_v, 3)
    alpha : float
        Blend parameter in [0, 1].
    rng : np.random.Generator

    Returns
    -------
    child : np.ndarray, shape (N_v, 3)
    """
    t = rng.uniform(0, 1, (len(parent_a), 1))
    child = (1 - t) * parent_a + t * parent_b
    return child


def crossover_uniform(parent_a, parent_b, rng):
    """Uniform crossover: each vertex is taken from either parent."""
    mask = rng.random(len(parent_a)) > 0.5
    child = parent_a.copy()
    child[mask] = parent_b[mask]
    return child


def crossover(parent_a, parent_b, alpha, rng):
    """Apply a randomly chosen crossover operator."""
    if rng.random() < 0.5:
        return crossover_blend(parent_a, parent_b, alpha, rng)
    else:
        return crossover_uniform(parent_a, parent_b, rng)


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def tournament_select(population, tournament_size, rng):
    """Select one individual via tournament selection.

    Parameters
    ----------
    population : list of Individual
    tournament_size : int
    rng : np.random.Generator

    Returns
    -------
    Individual
        Winner (lowest fitness).
    """
    indices = rng.choice(len(population), tournament_size, replace=False)
    best = min(indices, key=lambda i: population[i].fitness)
    return population[best]


# ---------------------------------------------------------------------------
# Main GA loop
# ---------------------------------------------------------------------------

def create_dumbbell_mesh(a_len=2.0, lobe_radius=0.8, n_subdivisions=2):
    """Create a dumbbell-shaped non-convex mesh for testing.

    Two spherical lobes connected along the x-axis.

    Parameters
    ----------
    a_len : float
        Half-length of the dumbbell (center-to-lobe distance).
    lobe_radius : float
        Radius of each lobe.
    n_subdivisions : int
        Icosphere subdivision level for each lobe.

    Returns
    -------
    TriMesh
        Dumbbell mesh.
    """
    lobe = create_sphere_mesh(n_subdivisions)

    # Left lobe
    verts_l = lobe.vertices * lobe_radius
    verts_l[:, 0] -= a_len

    # Right lobe
    verts_r = lobe.vertices * lobe_radius
    verts_r[:, 0] += a_len

    n_verts_l = len(verts_l)
    faces_r_shifted = lobe.faces + n_verts_l

    vertices = np.vstack([verts_l, verts_r])
    faces = np.vstack([lobe.faces, faces_r_shifted])

    normals, areas = compute_face_properties(vertices, faces)
    return TriMesh(vertices=vertices, faces=faces, normals=normals, areas=areas)


def run_genetic_solver(lightcurves, spin, config=None, initial_mesh=None):
    """Run evolutionary/genetic algorithm solver for non-convex shapes.

    Parameters
    ----------
    lightcurves : list of LightcurveData
        Observed lightcurves.
    spin : SpinState
        Known or estimated spin state (fixed during evolution).
    config : GAConfig, optional
        GA configuration. Uses defaults if None.
    initial_mesh : TriMesh, optional
        Seed mesh for initial population. If None, uses a sphere.

    Returns
    -------
    GAResult
        Best mesh, fitness, and convergence history.
    """
    if config is None:
        config = GAConfig()

    rng = np.random.default_rng(config.seed)

    # Initial mesh (template topology)
    if initial_mesh is None:
        initial_mesh = create_sphere_mesh(n_subdivisions=2)

    faces = initial_mesh.faces.copy()
    base_vertices = initial_mesh.vertices.copy()

    # Pre-compute body-frame directions (spin is fixed)
    precomputed = _precompute_body_dirs_ga(spin, lightcurves)

    # Compute scale of the mesh for sigma calibration
    mesh_scale = np.max(np.linalg.norm(base_vertices, axis=1))

    # Initialize population
    population = []
    for i in range(config.population_size):
        if i == 0:
            verts = base_vertices.copy()
        else:
            verts = mutate_gaussian(base_vertices,
                                    config.mutation_sigma * mesh_scale, rng)
        fitness = evaluate_fitness(verts, faces, spin, lightcurves,
                                   config.c_lambert, config.reg_weight,
                                   precomputed)
        population.append(Individual(vertices=verts, fitness=fitness))

    # Sort by fitness
    population.sort(key=lambda ind: ind.fitness)

    n_elite = max(1, int(config.population_size * config.elite_fraction))
    sigma = config.mutation_sigma * mesh_scale
    fitness_history = [population[0].fitness]
    generation_best = [population[0].fitness]

    if config.verbose:
        print(f"Gen 0: best fitness = {population[0].fitness:.6f}")

    for gen in range(1, config.n_generations + 1):
        new_population = []

        # Elitism: keep top individuals
        for i in range(n_elite):
            new_population.append(Individual(
                vertices=population[i].vertices.copy(),
                fitness=population[i].fitness
            ))

        # Fill remaining slots
        while len(new_population) < config.population_size:
            # Select parents
            parent_a = tournament_select(population, config.tournament_size, rng)
            parent_b = tournament_select(population, config.tournament_size, rng)

            # Crossover
            if rng.random() < config.crossover_rate:
                child_verts = crossover(parent_a.vertices, parent_b.vertices,
                                        config.blend_alpha, rng)
            else:
                child_verts = parent_a.vertices.copy()

            # Mutation
            if rng.random() < config.mutation_rate:
                child_verts = mutate(child_verts, sigma, rng)

            # Evaluate
            fitness = evaluate_fitness(child_verts, faces, spin, lightcurves,
                                       config.c_lambert, config.reg_weight,
                                       precomputed)
            new_population.append(Individual(vertices=child_verts, fitness=fitness))

        # Sort and update
        new_population.sort(key=lambda ind: ind.fitness)
        population = new_population[:config.population_size]

        # Decay mutation sigma
        sigma *= config.mutation_sigma_decay

        best_fit = population[0].fitness
        fitness_history.append(best_fit)
        generation_best.append(best_fit)

        if config.verbose and gen % 50 == 0:
            print(f"Gen {gen}: best fitness = {best_fit:.6f}, sigma = {sigma:.6f}")

    # Build final mesh
    best_verts = population[0].vertices
    normals, areas = compute_face_properties(best_verts, faces)
    best_mesh = TriMesh(vertices=best_verts, faces=faces,
                        normals=normals, areas=areas)

    return GAResult(
        mesh=best_mesh,
        spin=spin,
        fitness=population[0].fitness,
        fitness_history=fitness_history,
        generation_best=generation_best,
    )
