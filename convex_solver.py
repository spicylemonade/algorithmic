"""
Convex Inversion Solver (Module 2) — Kaasalainen-Torppa Method

Determines best-fit convex shape, pole direction, and sidereal period
by minimizing chi-squared residuals between observed and modeled lightcurves.
Uses facet-area parameterization with Levenberg-Marquardt optimization.

References:
    Kaasalainen & Torppa (2001) — shape determination
    Kaasalainen et al. (2001) — complete inverse problem
    Levenberg (1944), Marquardt (1963) — optimization algorithm
"""

import numpy as np
from scipy.optimize import minimize
from dataclasses import dataclass
from typing import List, Tuple, Optional
from forward_model import (TriMesh, create_sphere_mesh, compute_brightness,
                           generate_rotation_lightcurve, compute_face_properties,
                           scattering_lambert_lommel)
from geometry import SpinState, ecliptic_to_body_matrix


@dataclass
class LightcurveData:
    """Container for a single dense lightcurve."""
    jd: np.ndarray          # Julian Dates
    brightness: np.ndarray  # relative brightness (linear flux)
    weights: np.ndarray     # 1/sigma^2 weights
    sun_ecl: np.ndarray     # (N, 3) Sun directions in ecliptic
    obs_ecl: np.ndarray     # (N, 3) Observer directions in ecliptic


@dataclass
class InversionResult:
    """Result of convex inversion."""
    mesh: TriMesh
    spin: SpinState
    chi_squared: float
    chi_squared_history: List[float]
    period_landscape: Optional[np.ndarray] = None


def _precompute_body_dirs(spin, lc_data):
    """Pre-compute Sun and observer directions in body frame for all epochs.

    Parameters
    ----------
    spin : SpinState
    lc_data : LightcurveData

    Returns
    -------
    sun_body : np.ndarray, shape (N, 3)
    obs_body : np.ndarray, shape (N, 3)
    """
    N = len(lc_data.jd)
    sun_body = np.zeros((N, 3))
    obs_body = np.zeros((N, 3))
    for j in range(N):
        R = ecliptic_to_body_matrix(spin, lc_data.jd[j])
        sun_body[j] = R @ lc_data.sun_ecl[j]
        obs_body[j] = R @ lc_data.obs_ecl[j]
    return sun_body, obs_body


def _compute_model_lc(mesh, spin, lc_data, c_lambert=0.1, body_dirs=None):
    """Compute model lightcurve for given shape and spin.

    Parameters
    ----------
    mesh : TriMesh
        Convex shape model.
    spin : SpinState
        Spin state.
    lc_data : LightcurveData
        Observation data.
    c_lambert : float
        Lambert weight.
    body_dirs : tuple, optional
        Pre-computed (sun_body, obs_body) arrays.

    Returns
    -------
    model_brightness : np.ndarray
        Model brightness at each epoch.
    """
    from forward_model import generate_lightcurve_direct
    if body_dirs is not None:
        sun_body, obs_body = body_dirs
    else:
        sun_body, obs_body = _precompute_body_dirs(spin, lc_data)
    return generate_lightcurve_direct(mesh, sun_body, obs_body, c_lambert)


def chi_squared(mesh, spin, lightcurves, c_lambert=0.1, reg_weight=0.0,
                precomputed_dirs=None):
    """Compute chi-squared between observed and modeled lightcurves.

    Each lightcurve is independently normalized (fitted scaling factor).

    Parameters
    ----------
    mesh : TriMesh
        Shape model.
    spin : SpinState
        Spin state.
    lightcurves : list of LightcurveData
        Observed lightcurves.
    c_lambert : float
        Lambert weight.
    reg_weight : float
        Regularization weight for area smoothness.
    precomputed_dirs : list of tuple, optional
        Pre-computed body directions for each lightcurve.

    Returns
    -------
    chi2 : float
        Total chi-squared.
    """
    chi2 = 0.0
    n_total = 0
    for idx, lc in enumerate(lightcurves):
        bd = precomputed_dirs[idx] if precomputed_dirs else None
        model = _compute_model_lc(mesh, spin, lc, c_lambert, body_dirs=bd)
        if np.all(model == 0):
            chi2 += 1e10
            continue
        # Fit scaling factor: minimize sum w_i (obs_i - c * mod_i)^2
        # c = sum(w*obs*mod) / sum(w*mod^2)
        w = lc.weights
        c_fit = np.sum(w * lc.brightness * model) / (np.sum(w * model**2) + 1e-30)
        residuals = lc.brightness - c_fit * model
        chi2 += np.sum(w * residuals**2)
        n_total += len(lc.jd)

    # Regularization: penalize non-uniform areas
    if reg_weight > 0:
        mean_area = np.mean(mesh.areas)
        reg = reg_weight * np.sum((mesh.areas - mean_area)**2) / (mean_area**2 + 1e-30)
        chi2 += reg

    if n_total > 0:
        chi2 /= n_total

    return chi2


def optimize_shape(initial_mesh, spin, lightcurves, c_lambert=0.1,
                   reg_weight=0.01, max_iter=200, verbose=False):
    """Optimize facet areas to minimize chi-squared at fixed pole and period.

    Uses L-BFGS-B optimization on log-areas for non-negativity.

    Parameters
    ----------
    initial_mesh : TriMesh
        Starting shape (e.g., sphere).
    spin : SpinState
        Fixed spin state.
    lightcurves : list of LightcurveData
        Observed lightcurves.
    c_lambert : float
        Lambert weight.
    reg_weight : float
        Regularization weight.
    max_iter : int
        Maximum optimizer iterations.
    verbose : bool
        Print progress.

    Returns
    -------
    optimized_mesh : TriMesh
        Shape with optimized facet areas.
    chi2_final : float
        Final chi-squared.
    history : list of float
        Chi-squared history.
    """
    normals = initial_mesh.normals.copy()
    faces = initial_mesh.faces.copy()
    vertices = initial_mesh.vertices.copy()

    # Pre-compute body directions (spin is fixed, only areas change)
    precomputed = [_precompute_body_dirs(spin, lc) for lc in lightcurves]

    # Parameterize as log-areas
    log_areas0 = np.log(initial_mesh.areas + 1e-30)
    history = []

    def objective(log_areas):
        areas = np.exp(log_areas)
        mesh = TriMesh(vertices=vertices, faces=faces, normals=normals, areas=areas)
        chi2 = chi_squared(mesh, spin, lightcurves, c_lambert, reg_weight,
                           precomputed_dirs=precomputed)
        history.append(chi2)
        return chi2

    result = minimize(objective, log_areas0, method='L-BFGS-B',
                      options={'maxiter': max_iter, 'ftol': 1e-12})

    areas_opt = np.exp(result.x)

    # Reconstruct vertex positions from optimized face areas.
    # Each vertex radial distance is proportional to the mean area of
    # adjacent faces, giving a convex shape approximation from the
    # Gaussian image (Kaasalainen & Torppa 2001).
    n_verts = len(vertices)
    vertex_weight = np.zeros(n_verts)
    vertex_count = np.zeros(n_verts)
    for fi, face in enumerate(faces):
        for vi in face:
            vertex_weight[vi] += areas_opt[fi]
            vertex_count[vi] += 1
    vertex_count = np.maximum(vertex_count, 1)
    mean_area = np.mean(areas_opt)
    radial_scale = (vertex_weight / vertex_count) / (mean_area + 1e-30)
    # Cube root gives better shape proportionality for surface area
    radial_scale = np.cbrt(np.maximum(radial_scale, 1e-30))
    new_vertices = vertices * radial_scale[:, np.newaxis]

    optimized_mesh = TriMesh(vertices=new_vertices, faces=faces,
                             normals=normals, areas=areas_opt)
    chi2_final = result.fun

    if verbose:
        print(f"  Shape optimization: chi2={chi2_final:.6f}, "
              f"iterations={result.nit}, success={result.success}")

    return optimized_mesh, chi2_final, history


def period_search(initial_mesh, base_spin, lightcurves, p_min, p_max, n_periods,
                  c_lambert=0.1, reg_weight=0.01, opt_iter=50, verbose=False):
    """Scan period range and find best-fit period via chi-squared landscape.

    Parameters
    ----------
    initial_mesh : TriMesh
        Starting shape for each trial.
    base_spin : SpinState
        Spin state template (period will be varied).
    lightcurves : list of LightcurveData
        Observed lightcurves.
    p_min, p_max : float
        Period range (hours).
    n_periods : int
        Number of period trial values.
    c_lambert : float
    reg_weight : float
    opt_iter : int
        Shape optimization iterations per period trial.
    verbose : bool

    Returns
    -------
    best_period : float
        Best-fit period (hours).
    periods : np.ndarray
        Array of trial periods.
    chi2_landscape : np.ndarray
        Chi-squared at each trial period.
    """
    periods = np.linspace(p_min, p_max, n_periods)
    chi2_landscape = np.zeros(n_periods)

    for idx, period in enumerate(periods):
        spin_trial = SpinState(
            lambda_deg=base_spin.lambda_deg,
            beta_deg=base_spin.beta_deg,
            period_hours=period,
            jd0=base_spin.jd0,
            phi0=base_spin.phi0
        )
        _, chi2, _ = optimize_shape(initial_mesh, spin_trial, lightcurves,
                                    c_lambert, reg_weight, opt_iter)
        chi2_landscape[idx] = chi2
        if verbose and idx % 10 == 0:
            print(f"  Period {period:.6f} h: chi2={chi2:.6f}")

    best_idx = np.argmin(chi2_landscape)
    best_period = periods[best_idx]
    return best_period, periods, chi2_landscape


def pole_search(initial_mesh, base_spin, lightcurves, n_lambda=12, n_beta=6,
                c_lambert=0.1, reg_weight=0.01, opt_iter=50, verbose=False):
    """Grid search over pole directions.

    Parameters
    ----------
    initial_mesh : TriMesh
        Starting shape.
    base_spin : SpinState
        Spin state template (pole will be varied, period fixed).
    lightcurves : list of LightcurveData
    n_lambda : int
        Number of longitude steps.
    n_beta : int
        Number of latitude steps.
    c_lambert : float
    reg_weight : float
    opt_iter : int
    verbose : bool

    Returns
    -------
    best_lambda : float
        Best-fit pole longitude (degrees).
    best_beta : float
        Best-fit pole latitude (degrees).
    grid : np.ndarray, shape (n_lambda * n_beta * 2, 3)
        All (lambda, beta, chi2) values.
    """
    lambdas = np.linspace(0, 360, n_lambda, endpoint=False)
    betas = np.linspace(-90, 90, 2 * n_beta + 1)[1::2]  # avoid exact poles

    results = []
    best_chi2 = np.inf
    best_lam, best_bet = 0.0, 0.0

    for lam in lambdas:
        for bet in betas:
            spin_trial = SpinState(
                lambda_deg=lam,
                beta_deg=bet,
                period_hours=base_spin.period_hours,
                jd0=base_spin.jd0,
                phi0=base_spin.phi0
            )
            _, chi2, _ = optimize_shape(initial_mesh, spin_trial, lightcurves,
                                        c_lambert, reg_weight, opt_iter)
            results.append([lam, bet, chi2])
            if chi2 < best_chi2:
                best_chi2 = chi2
                best_lam, best_bet = lam, bet
            if verbose:
                print(f"  Pole ({lam:.0f}, {bet:.0f}): chi2={chi2:.6f}")

    grid = np.array(results)
    return best_lam, best_bet, grid


def run_convex_inversion(lightcurves, p_min, p_max, n_periods=100,
                         n_lambda=12, n_beta=6, n_subdivisions=2,
                         c_lambert=0.1, reg_weight=0.01,
                         max_shape_iter=200, verbose=False):
    """Full convex inversion pipeline: period search -> pole search -> shape optimization.

    Parameters
    ----------
    lightcurves : list of LightcurveData
        Observed lightcurves.
    p_min, p_max : float
        Period search range (hours).
    n_periods : int
    n_lambda, n_beta : int
        Pole grid resolution.
    n_subdivisions : int
        Icosphere subdivision level for shape model.
    c_lambert : float
    reg_weight : float
    max_shape_iter : int
    verbose : bool

    Returns
    -------
    InversionResult
        Complete inversion result.
    """
    # Initial sphere
    sphere = create_sphere_mesh(n_subdivisions)
    jd0 = lightcurves[0].jd[0]

    # Step 1: Coarse period search at initial pole (0, 0)
    base_spin = SpinState(lambda_deg=0, beta_deg=0, period_hours=(p_min+p_max)/2,
                          jd0=jd0)
    if verbose:
        print("Step 1: Period search...")
    best_period, periods, period_chi2 = period_search(
        sphere, base_spin, lightcurves, p_min, p_max, n_periods,
        c_lambert, reg_weight, opt_iter=30, verbose=verbose
    )
    if verbose:
        print(f"  Best period: {best_period:.6f} h")

    # Step 2: Pole search at best period
    base_spin = SpinState(lambda_deg=0, beta_deg=0, period_hours=best_period,
                          jd0=jd0)
    if verbose:
        print("Step 2: Pole search...")
    best_lam, best_bet, pole_grid = pole_search(
        sphere, base_spin, lightcurves, n_lambda, n_beta,
        c_lambert, reg_weight, opt_iter=50, verbose=verbose
    )
    if verbose:
        print(f"  Best pole: ({best_lam:.1f}, {best_bet:.1f})")

    # Step 3: Fine period refinement around best period
    dp = (p_max - p_min) / n_periods * 2
    base_spin = SpinState(lambda_deg=best_lam, beta_deg=best_bet,
                          period_hours=best_period, jd0=jd0)
    if verbose:
        print("Step 3: Fine period refinement...")
    best_period, _, _ = period_search(
        sphere, base_spin, lightcurves,
        best_period - dp, best_period + dp, 50,
        c_lambert, reg_weight, opt_iter=50, verbose=verbose
    )
    if verbose:
        print(f"  Refined period: {best_period:.8f} h")

    # Step 4: Full shape optimization at best pole + period
    best_spin = SpinState(lambda_deg=best_lam, beta_deg=best_bet,
                          period_hours=best_period, jd0=jd0)
    if verbose:
        print("Step 4: Shape optimization...")
    opt_mesh, chi2_final, history = optimize_shape(
        sphere, best_spin, lightcurves, c_lambert, reg_weight,
        max_shape_iter, verbose=verbose
    )

    return InversionResult(
        mesh=opt_mesh,
        spin=best_spin,
        chi_squared=chi2_final,
        chi_squared_history=history,
        period_landscape=np.column_stack([periods, period_chi2])
    )
