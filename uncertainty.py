"""
Uncertainty Quantification Module (Module 11)

Estimates uncertainties for spin vectors (pole direction, period) and
shape models via bootstrap resampling and chi-squared landscape analysis.

References:
    Kaasalainen & Torppa (2001) — parameter uncertainty from chi2 landscape
    Hanus et al. (2011) — bootstrap-based uncertainty for pole direction
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from forward_model import (TriMesh, create_sphere_mesh, compute_face_properties,
                           generate_lightcurve_direct)
from geometry import SpinState, ecliptic_to_body_matrix
from convex_solver import (LightcurveData, optimize_shape, chi_squared,
                           _precompute_body_dirs, period_search)


@dataclass
class UncertaintyResult:
    """Results of uncertainty quantification."""
    # Pole uncertainty
    pole_lambda_mean: float
    pole_beta_mean: float
    pole_lambda_std: float
    pole_beta_std: float
    pole_samples: np.ndarray  # (n_bootstrap, 2) — (lambda, beta) samples

    # Period uncertainty
    period_mean: float
    period_std: float
    period_samples: np.ndarray  # (n_bootstrap,)

    # Shape uncertainty (per-vertex variance)
    vertex_variance: np.ndarray  # (N_v,) — per-vertex position variance
    vertex_std_map: np.ndarray   # (N_v,) — per-vertex RMS displacement

    # Chi-squared landscape
    period_landscape: Optional[np.ndarray] = None  # (n_periods, 2)


# ---------------------------------------------------------------------------
# Bootstrap resampling
# ---------------------------------------------------------------------------

def _resample_lightcurve(lc, rng):
    """Bootstrap-resample a single lightcurve (resample data points with replacement).

    Parameters
    ----------
    lc : LightcurveData
    rng : np.random.Generator

    Returns
    -------
    LightcurveData
        Resampled lightcurve.
    """
    n = len(lc.jd)
    indices = rng.choice(n, size=n, replace=True)
    return LightcurveData(
        jd=lc.jd[indices],
        brightness=lc.brightness[indices],
        weights=lc.weights[indices],
        sun_ecl=lc.sun_ecl[indices],
        obs_ecl=lc.obs_ecl[indices],
    )


def _resample_lightcurves(lightcurves, rng):
    """Bootstrap-resample all lightcurves."""
    return [_resample_lightcurve(lc, rng) for lc in lightcurves]


def _add_noise_lightcurve(lc, noise_sigma, rng):
    """Add Gaussian noise to lightcurve brightness values.

    Parameters
    ----------
    lc : LightcurveData
    noise_sigma : float
        Noise standard deviation as fraction of mean brightness.
    rng : np.random.Generator

    Returns
    -------
    LightcurveData
        Noisy lightcurve.
    """
    mean_b = np.mean(lc.brightness)
    noise = rng.normal(0, noise_sigma * mean_b, len(lc.brightness))
    return LightcurveData(
        jd=lc.jd.copy(),
        brightness=lc.brightness + noise,
        weights=lc.weights.copy(),
        sun_ecl=lc.sun_ecl.copy(),
        obs_ecl=lc.obs_ecl.copy(),
    )


# ---------------------------------------------------------------------------
# Period uncertainty from chi-squared landscape
# ---------------------------------------------------------------------------

def estimate_period_uncertainty(periods, chi2_values, best_chi2=None):
    """Estimate period uncertainty from chi-squared landscape width.

    Uses the Delta-chi2 = 1 criterion: the 1-sigma interval is where
    chi2 < chi2_min + 1 (for a single parameter).

    Parameters
    ----------
    periods : np.ndarray
        Trial periods (hours).
    chi2_values : np.ndarray
        Chi-squared at each trial period.
    best_chi2 : float, optional
        Minimum chi-squared. If None, uses min of chi2_values.

    Returns
    -------
    period_sigma : float
        Estimated 1-sigma period uncertainty (hours).
    """
    if best_chi2 is None:
        best_chi2 = np.min(chi2_values)

    # Normalise so that the minimum is at 0
    delta_chi2 = chi2_values - best_chi2

    # Find the 1-sigma interval
    mask = delta_chi2 <= 1.0
    if np.sum(mask) < 2:
        # If < 2 points within delta_chi2=1, use a wider threshold
        mask = delta_chi2 <= np.min(delta_chi2) + 1.0

    if np.sum(mask) >= 2:
        p_in = periods[mask]
        period_sigma = (p_in.max() - p_in.min()) / 2.0
    else:
        # Fallback: use the full width at half-max of the chi2 valley
        half_max = best_chi2 + (np.max(chi2_values) - best_chi2) / 2.0
        mask_hm = chi2_values <= half_max
        if np.sum(mask_hm) >= 2:
            p_hm = periods[mask_hm]
            period_sigma = (p_hm.max() - p_hm.min()) / 2.0
        else:
            period_sigma = (periods[-1] - periods[0]) / len(periods)

    return period_sigma


# ---------------------------------------------------------------------------
# Main bootstrap uncertainty estimation
# ---------------------------------------------------------------------------

def estimate_uncertainties(lightcurves, spin, n_bootstrap=100,
                           n_subdivisions=1, c_lambert=0.1,
                           reg_weight=0.01, max_iter=100,
                           p_min=None, p_max=None, n_periods=50,
                           noise_sigma=0.005, seed=42, verbose=False):
    """Estimate uncertainties via bootstrap resampling.

    For each bootstrap iteration:
    1. Resample lightcurve data points with replacement.
    2. Optionally add noise.
    3. Re-run shape optimization at fixed spin.
    4. Record optimised pole, period, and vertex positions.

    Parameters
    ----------
    lightcurves : list of LightcurveData
        Original lightcurves.
    spin : SpinState
        Best-fit spin state.
    n_bootstrap : int
        Number of bootstrap iterations (>= 100).
    n_subdivisions : int
        Icosphere subdivision for shape model.
    c_lambert : float
    reg_weight : float
    max_iter : int
        Shape optimization iterations per bootstrap.
    p_min, p_max : float, optional
        Period search range. If None, skip period uncertainty.
    n_periods : int
        Number of trial periods for landscape.
    noise_sigma : float
        Gaussian noise level (fraction of mean brightness).
    seed : int
    verbose : bool

    Returns
    -------
    UncertaintyResult
    """
    rng = np.random.default_rng(seed)
    sphere = create_sphere_mesh(n_subdivisions)
    n_verts = len(sphere.vertices)

    pole_samples = np.zeros((n_bootstrap, 2))
    period_samples = np.zeros(n_bootstrap)
    vertex_samples = np.zeros((n_bootstrap, n_verts, 3))

    # Period landscape (computed once on original data)
    period_landscape = None
    if p_min is not None and p_max is not None:
        _, periods_arr, chi2_arr = period_search(
            sphere, spin, lightcurves, p_min, p_max, n_periods,
            c_lambert, reg_weight, opt_iter=max_iter // 2
        )
        period_landscape = np.column_stack([periods_arr, chi2_arr])

    for i in range(n_bootstrap):
        # Resample + add noise
        resampled = _resample_lightcurves(lightcurves, rng)
        noisy = [_add_noise_lightcurve(lc, noise_sigma, rng) for lc in resampled]

        # Optimize shape at fixed spin
        opt_mesh, chi2, _ = optimize_shape(
            sphere, spin, noisy,
            c_lambert=c_lambert, reg_weight=reg_weight,
            max_iter=max_iter, verbose=False
        )

        pole_samples[i] = [spin.lambda_deg, spin.beta_deg]
        period_samples[i] = spin.period_hours
        vertex_samples[i] = opt_mesh.vertices

        if verbose and (i + 1) % 20 == 0:
            print(f"  Bootstrap {i+1}/{n_bootstrap}: chi2={chi2:.6f}")

    # Compute statistics
    pole_lambda_mean = np.mean(pole_samples[:, 0])
    pole_beta_mean = np.mean(pole_samples[:, 1])
    pole_lambda_std = np.std(pole_samples[:, 0])
    pole_beta_std = np.std(pole_samples[:, 1])

    period_mean = np.mean(period_samples)
    period_std = np.std(period_samples)

    # Period uncertainty from landscape if available
    if period_landscape is not None:
        period_sigma_landscape = estimate_period_uncertainty(
            period_landscape[:, 0], period_landscape[:, 1]
        )
        period_std = max(period_std, period_sigma_landscape)

    # Per-vertex variance: mean displacement from mean shape
    mean_shape = np.mean(vertex_samples, axis=0)  # (N_v, 3)
    displacements = vertex_samples - mean_shape[np.newaxis, :]  # (n_boot, N_v, 3)
    vertex_variance = np.mean(np.sum(displacements ** 2, axis=2), axis=0)  # (N_v,)
    vertex_std_map = np.sqrt(vertex_variance)

    return UncertaintyResult(
        pole_lambda_mean=pole_lambda_mean,
        pole_beta_mean=pole_beta_mean,
        pole_lambda_std=pole_lambda_std,
        pole_beta_std=pole_beta_std,
        pole_samples=pole_samples,
        period_mean=period_mean,
        period_std=period_std,
        period_samples=period_samples,
        vertex_variance=vertex_variance,
        vertex_std_map=vertex_std_map,
        period_landscape=period_landscape,
    )


def estimate_uncertainties_with_pole(lightcurves, spin, n_bootstrap=100,
                                      n_subdivisions=1, c_lambert=0.1,
                                      reg_weight=0.01, max_iter=50,
                                      pole_n_lambda=6, pole_n_beta=3,
                                      noise_sigma=0.005, seed=42,
                                      verbose=False):
    """Estimate uncertainties including pole resampling.

    For each bootstrap iteration, re-runs a coarse pole search in addition
    to shape optimization, yielding pole direction scatter.

    Parameters
    ----------
    lightcurves : list of LightcurveData
    spin : SpinState
        Best-fit spin state (used as initial guess and for period).
    n_bootstrap : int
    n_subdivisions : int
    c_lambert : float
    reg_weight : float
    max_iter : int
    pole_n_lambda, pole_n_beta : int
        Pole grid resolution (kept small for speed).
    noise_sigma : float
    seed : int
    verbose : bool

    Returns
    -------
    UncertaintyResult
    """
    from convex_solver import pole_search as convex_pole_search

    rng = np.random.default_rng(seed)
    sphere = create_sphere_mesh(n_subdivisions)
    n_verts = len(sphere.vertices)

    pole_samples = np.zeros((n_bootstrap, 2))
    period_samples = np.zeros(n_bootstrap)
    vertex_samples = np.zeros((n_bootstrap, n_verts, 3))

    for i in range(n_bootstrap):
        resampled = _resample_lightcurves(lightcurves, rng)
        noisy = [_add_noise_lightcurve(lc, noise_sigma, rng) for lc in resampled]

        # Coarse pole search
        best_lam, best_bet, _ = convex_pole_search(
            sphere, spin, noisy,
            n_lambda=pole_n_lambda, n_beta=pole_n_beta,
            c_lambert=c_lambert, reg_weight=reg_weight,
            opt_iter=max_iter // 2, verbose=False
        )

        trial_spin = SpinState(
            lambda_deg=best_lam, beta_deg=best_bet,
            period_hours=spin.period_hours, jd0=spin.jd0, phi0=spin.phi0
        )

        # Shape optimization at found pole
        opt_mesh, chi2, _ = optimize_shape(
            sphere, trial_spin, noisy,
            c_lambert=c_lambert, reg_weight=reg_weight,
            max_iter=max_iter, verbose=False
        )

        pole_samples[i] = [best_lam, best_bet]
        period_samples[i] = spin.period_hours
        vertex_samples[i] = opt_mesh.vertices

        if verbose and (i + 1) % 20 == 0:
            print(f"  Bootstrap {i+1}/{n_bootstrap}: "
                  f"pole=({best_lam:.0f},{best_bet:.0f}), chi2={chi2:.6f}")

    pole_lambda_mean = np.mean(pole_samples[:, 0])
    pole_beta_mean = np.mean(pole_samples[:, 1])
    pole_lambda_std = np.std(pole_samples[:, 0])
    pole_beta_std = np.std(pole_samples[:, 1])

    period_mean = np.mean(period_samples)
    period_std = np.std(period_samples)

    mean_shape = np.mean(vertex_samples, axis=0)
    displacements = vertex_samples - mean_shape[np.newaxis, :]
    vertex_variance = np.mean(np.sum(displacements ** 2, axis=2), axis=0)
    vertex_std_map = np.sqrt(vertex_variance)

    return UncertaintyResult(
        pole_lambda_mean=pole_lambda_mean,
        pole_beta_mean=pole_beta_mean,
        pole_lambda_std=pole_lambda_std,
        pole_beta_std=pole_beta_std,
        pole_samples=pole_samples,
        period_mean=period_mean,
        period_std=period_std,
        period_samples=period_samples,
        vertex_variance=vertex_variance,
        vertex_std_map=vertex_std_map,
    )
