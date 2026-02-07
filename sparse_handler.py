"""
Sparse Photometric Data Handler (Module 4)

Parses, calibrates, and integrates sparse photometric data from surveys
(Gaia DR3, ZTF, Pan-STARRS) into the inversion objective function.

References:
    Durech et al. (2009) — sparse+dense combined inversion
    Muinonen et al. (2010) — H,G1,G2 phase curve model
    Cellino et al. (2009) — genetic inversion of sparse data
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import csv
import os

from geometry import (OrbitalElements, SpinState, compute_geometry,
                      ecliptic_to_body_matrix, orbital_position,
                      earth_position_approx)
from forward_model import (TriMesh, compute_brightness,
                           generate_lightcurve_direct, create_sphere_mesh)
from convex_solver import (LightcurveData, chi_squared as dense_chi_squared,
                           optimize_shape, _precompute_body_dirs)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class SparseObservation:
    """A single sparse photometric observation."""
    jd: float              # Julian Date of observation
    mag: float             # observed apparent magnitude
    mag_err: float         # magnitude uncertainty (1-sigma)
    filter_name: str       # photometric filter identifier
    phase_angle: float = 0.0   # Sun-target-observer angle (radians)
    r_helio: float = 1.0       # heliocentric distance (AU)
    r_geo: float = 1.0         # geocentric distance (AU)


@dataclass
class SparseDataset:
    """Collection of sparse observations, possibly from multiple filters."""
    observations: List[SparseObservation] = field(default_factory=list)
    source: str = ""       # e.g. "GaiaDR3", "ZTF", "PanSTARRS"
    target_id: str = ""    # asteroid identifier

    @property
    def n_obs(self):
        return len(self.observations)

    def jd_array(self):
        return np.array([o.jd for o in self.observations])

    def mag_array(self):
        return np.array([o.mag for o in self.observations])

    def mag_err_array(self):
        return np.array([o.mag_err for o in self.observations])

    def phase_angle_array(self):
        return np.array([o.phase_angle for o in self.observations])

    def r_helio_array(self):
        return np.array([o.r_helio for o in self.observations])

    def r_geo_array(self):
        return np.array([o.r_geo for o in self.observations])


# ---------------------------------------------------------------------------
# H-G phase curve model  (IAU standard, Bowell et al. 1989)
# ---------------------------------------------------------------------------

def _phi1(alpha):
    """Compute phi1 basis function for H-G model.

    Parameters
    ----------
    alpha : np.ndarray
        Phase angle in radians.

    Returns
    -------
    phi1 : np.ndarray
        phi1 values.
    """
    alpha = np.asarray(alpha, dtype=np.float64)
    half = np.clip(alpha / 2.0, 0.0, np.pi / 2.0 - 1e-10)
    tan_half = np.tan(half)
    return np.exp(-3.33 * tan_half ** 0.63)


def _phi2(alpha):
    """Compute phi2 basis function for H-G model.

    Parameters
    ----------
    alpha : np.ndarray
        Phase angle in radians.

    Returns
    -------
    phi2 : np.ndarray
        phi2 values.
    """
    alpha = np.asarray(alpha, dtype=np.float64)
    half = np.clip(alpha / 2.0, 0.0, np.pi / 2.0 - 1e-10)
    tan_half = np.tan(half)
    return np.exp(-1.87 * tan_half ** 1.22)


def hg_phase_function(alpha, H, G):
    """Compute apparent reduced magnitude using the IAU H-G phase curve model.

    V(alpha) = H - 2.5 * log10( G * phi1(alpha) + (1 - G) * phi2(alpha) )

    Parameters
    ----------
    alpha : float or np.ndarray
        Phase angle in radians.
    H : float
        Absolute magnitude.
    G : float
        Slope parameter (typically 0.0 -- 0.5, default ~0.15).

    Returns
    -------
    V : float or np.ndarray
        Predicted reduced magnitude V(1, 1, alpha).
    """
    alpha = np.asarray(alpha, dtype=np.float64)
    p1 = _phi1(alpha)
    p2 = _phi2(alpha)
    combined = G * p1 + (1.0 - G) * p2
    # Guard against log of zero/negative
    combined = np.maximum(combined, 1e-30)
    V = H - 2.5 * np.log10(combined)
    return V


# ---------------------------------------------------------------------------
# H-G1-G2 three-parameter phase curve model (Muinonen et al. 2010)
# ---------------------------------------------------------------------------

def _phi3(alpha):
    """Linear basis function phi3(alpha) = 1 - alpha / pi.

    Parameters
    ----------
    alpha : np.ndarray
        Phase angle in radians.

    Returns
    -------
    phi3 : np.ndarray
    """
    alpha = np.asarray(alpha, dtype=np.float64)
    return 1.0 - alpha / np.pi


def hg12_phase_function(alpha, H, G1, G2):
    """Compute reduced magnitude using the three-parameter H-G1-G2 model.

    V(alpha) = H - 2.5 * log10( G1 * phi1(alpha) + G2 * phi2(alpha)
                                 + (1 - G1 - G2) * phi3(alpha) )

    Parameters
    ----------
    alpha : float or np.ndarray
        Phase angle in radians.
    H : float
        Absolute magnitude.
    G1 : float
        First slope parameter.
    G2 : float
        Second slope parameter.

    Returns
    -------
    V : float or np.ndarray
        Predicted reduced magnitude V(1, 1, alpha).
    """
    alpha = np.asarray(alpha, dtype=np.float64)
    p1 = _phi1(alpha)
    p2 = _phi2(alpha)
    p3 = _phi3(alpha)
    G3 = 1.0 - G1 - G2
    combined = G1 * p1 + G2 * p2 + G3 * p3
    combined = np.maximum(combined, 1e-30)
    V = H - 2.5 * np.log10(combined)
    return V


# ---------------------------------------------------------------------------
# Magnitude calibration — remove phase curve trend
# ---------------------------------------------------------------------------

def calibrate_sparse_magnitudes(mag_observed, phase_angles, r_helio, r_geo,
                                H, G_params, model='HG'):
    """Remove phase-curve and distance effects to obtain reduced magnitudes.

    The observed magnitude includes distance modulus and phase curve:
        m = H + 5*log10(r*delta) - 2.5*log10(phase_term)

    The *reduced* magnitude is the rotational brightness variation only:
        m_reduced = m_obs - 5*log10(r*delta) - phase_correction

    where phase_correction = V_model(alpha) - H = -2.5*log10(phase_term).

    Parameters
    ----------
    mag_observed : np.ndarray
        Observed apparent magnitudes.
    phase_angles : np.ndarray
        Phase angles in radians.
    r_helio : np.ndarray
        Heliocentric distance (AU).
    r_geo : np.ndarray
        Geocentric distance (AU).
    H : float
        Absolute magnitude.
    G_params : float or tuple
        If model='HG': single G parameter.
        If model='HG12': tuple (G1, G2).
    model : str
        'HG' or 'HG12'.

    Returns
    -------
    mag_reduced : np.ndarray
        Reduced magnitudes (distance and phase corrected).
    """
    mag_observed = np.asarray(mag_observed, dtype=np.float64)
    phase_angles = np.asarray(phase_angles, dtype=np.float64)
    r_helio = np.asarray(r_helio, dtype=np.float64)
    r_geo = np.asarray(r_geo, dtype=np.float64)

    # Distance modulus: 5 * log10(r_helio * r_geo)
    dist_mod = 5.0 * np.log10(np.maximum(r_helio * r_geo, 1e-30))

    # Phase correction: V_model(alpha) - H
    if model == 'HG':
        G = G_params if np.isscalar(G_params) else G_params[0]
        phase_correction = hg_phase_function(phase_angles, 0.0, G)
        # hg_phase_function(alpha, H=0, G) gives -2.5*log10(phase_term)
    elif model == 'HG12':
        G1, G2 = G_params
        phase_correction = hg12_phase_function(phase_angles, 0.0, G1, G2)
    else:
        raise ValueError(f"Unknown phase curve model: {model}")

    # Reduced magnitude: remove distance and phase effects
    # m_obs = H + dist_mod + phase_correction_from_H
    # => m_reduced = m_obs - dist_mod - phase_correction
    mag_reduced = mag_observed - dist_mod - phase_correction
    return mag_reduced


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_gaia_sso_csv(filepath):
    """Parse Gaia DR3 Solar System Object photometry CSV.

    Expected CSV columns (Gaia archive format):
        source_id, transit_id, observation_time (BJD-2455197.5 days),
        g_mag, g_flux, g_flux_error, x, y, z (heliocentric, AU),
        x_earth, y_earth, z_earth (geocentric, AU)

    Falls back to a simplified format with columns:
        jd, mag, mag_err, phase_angle_deg, r_helio, r_geo

    Parameters
    ----------
    filepath : str
        Path to CSV file.

    Returns
    -------
    SparseDataset
        Parsed sparse dataset.
    """
    dataset = SparseDataset(source="GaiaDR3", target_id=os.path.basename(filepath))
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            return dataset

        # Detect format
        has_gaia_cols = ('g_mag' in fieldnames and 'observation_time' in fieldnames)
        has_simple_cols = ('jd' in fieldnames and 'mag' in fieldnames)

        if has_gaia_cols:
            for row in reader:
                try:
                    # Gaia observation_time is BJD - 2455197.5
                    bjd_offset = float(row['observation_time'])
                    jd = bjd_offset + 2455197.5

                    mag = float(row['g_mag'])
                    flux_err = float(row.get('g_flux_error', '0.01'))
                    flux = float(row.get('g_flux', '1.0'))
                    # Convert flux error to magnitude error
                    mag_err = (2.5 / np.log(10)) * abs(flux_err / max(flux, 1e-30))
                    mag_err = max(mag_err, 0.001)

                    # Compute distances and phase angle from positions
                    ast_pos = np.array([float(row['x']), float(row['y']),
                                        float(row['z'])])
                    earth_pos = np.array([float(row['x_earth']),
                                          float(row['y_earth']),
                                          float(row['z_earth'])])
                    r_helio = np.linalg.norm(ast_pos)
                    obs_vec = earth_pos - ast_pos
                    r_geo = np.linalg.norm(obs_vec)
                    sun_dir = -ast_pos / max(r_helio, 1e-30)
                    obs_dir = obs_vec / max(r_geo, 1e-30)
                    cos_alpha = np.clip(np.dot(sun_dir, obs_dir), -1, 1)
                    phase_angle = np.arccos(cos_alpha)

                    obs = SparseObservation(
                        jd=jd, mag=mag, mag_err=mag_err,
                        filter_name='G',
                        phase_angle=phase_angle,
                        r_helio=r_helio, r_geo=r_geo
                    )
                    dataset.observations.append(obs)
                except (ValueError, KeyError):
                    continue

        elif has_simple_cols:
            for row in reader:
                try:
                    jd = float(row['jd'])
                    mag = float(row['mag'])
                    mag_err = float(row.get('mag_err', '0.02'))
                    phase_deg = float(row.get('phase_angle_deg', '0.0'))
                    r_h = float(row.get('r_helio', '1.0'))
                    r_g = float(row.get('r_geo', '1.0'))
                    filt = row.get('filter', 'G')

                    obs = SparseObservation(
                        jd=jd, mag=mag, mag_err=mag_err,
                        filter_name=filt,
                        phase_angle=np.radians(phase_deg),
                        r_helio=r_h, r_geo=r_g
                    )
                    dataset.observations.append(obs)
                except (ValueError, KeyError):
                    continue

    return dataset


def parse_generic_sparse(filepath):
    """Parse generic sparse photometry CSV.

    Expected columns: jd, mag, mag_err, filter
    Optional columns: phase_angle_deg, r_helio, r_geo

    Parameters
    ----------
    filepath : str
        Path to CSV file.

    Returns
    -------
    SparseDataset
        Parsed sparse dataset.
    """
    dataset = SparseDataset(source="generic", target_id=os.path.basename(filepath))
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                jd = float(row['jd'])
                mag = float(row['mag'])
                mag_err = float(row.get('mag_err', '0.02'))
                filt = row.get('filter', 'V')
                phase_deg = float(row.get('phase_angle_deg', '0.0'))
                r_h = float(row.get('r_helio', '1.0'))
                r_g = float(row.get('r_geo', '1.0'))

                obs = SparseObservation(
                    jd=jd, mag=mag, mag_err=mag_err,
                    filter_name=filt,
                    phase_angle=np.radians(phase_deg),
                    r_helio=r_h, r_geo=r_g
                )
                dataset.observations.append(obs)
            except (ValueError, KeyError):
                continue

    return dataset


# ---------------------------------------------------------------------------
# Convert sparse observations to LightcurveData format
# ---------------------------------------------------------------------------

def compute_sparse_geometry(jd_array, orbital_elements, spin):
    """Compute viewing geometry for sparse epochs from orbital elements.

    Parameters
    ----------
    jd_array : np.ndarray
        Julian Dates of sparse observations.
    orbital_elements : OrbitalElements
        Asteroid orbital elements.
    spin : SpinState
        Spin state.

    Returns
    -------
    dict
        Same format as geometry.compute_geometry output.
    """
    return compute_geometry(orbital_elements, spin, jd_array)


def create_sparse_lightcurve_data(sparse_data, orbital_elements, spin):
    """Convert sparse observations into LightcurveData format.

    Each sparse observation is treated as a single-point "lightcurve" in
    terms of geometry. We pack all sparse points into one LightcurveData
    object with brightness derived from magnitudes and weights from
    magnitude uncertainties.

    Parameters
    ----------
    sparse_data : SparseDataset
        Parsed sparse observations.
    orbital_elements : OrbitalElements
        Asteroid orbital elements.
    spin : SpinState
        Spin state.

    Returns
    -------
    LightcurveData
        Sparse observations in the format expected by convex_solver.
    """
    if sparse_data.n_obs == 0:
        raise ValueError("SparseDataset contains no observations.")

    jd = sparse_data.jd_array()
    mags = sparse_data.mag_array()
    mag_errs = sparse_data.mag_err_array()

    # Compute geometry from orbital elements
    geo = compute_geometry(orbital_elements, spin, jd)

    # Convert magnitudes to relative brightness (linear flux)
    # brightness = 10^(-0.4 * mag)  (arbitrary zero-point)
    brightness = np.power(10.0, -0.4 * mags)

    # Apply distance correction:  m_reduced = m - 5*log10(r*delta)
    # => brightness_reduced = brightness / (r*delta)^2  ... in flux space
    r_h = geo['r_helio']
    r_g = geo['r_geo']
    dist_factor = (r_h * r_g) ** 2
    brightness_reduced = brightness * dist_factor

    # Weights: in magnitude space sigma_mag -> in flux space
    # sigma_flux / flux ~ (ln10/2.5) * sigma_mag
    # w = 1/sigma_flux^2
    rel_flux_err = (np.log(10.0) / 2.5) * mag_errs
    flux_sigma = brightness_reduced * rel_flux_err
    weights = 1.0 / (flux_sigma ** 2 + 1e-30)

    # Sun and observer directions in ecliptic frame
    ast_pos = orbital_position(orbital_elements, jd)
    earth_pos = earth_position_approx(jd)

    r_ast_norm = np.linalg.norm(ast_pos, axis=-1, keepdims=True)
    sun_ecl = -ast_pos / np.maximum(r_ast_norm, 1e-30)

    obs_vec = earth_pos - ast_pos
    obs_norm = np.linalg.norm(obs_vec, axis=-1, keepdims=True)
    obs_ecl = obs_vec / np.maximum(obs_norm, 1e-30)

    return LightcurveData(
        jd=jd,
        brightness=brightness_reduced,
        weights=weights,
        sun_ecl=sun_ecl,
        obs_ecl=obs_ecl
    )


# ---------------------------------------------------------------------------
# Combined chi-squared: dense + sparse
# ---------------------------------------------------------------------------

def sparse_chi_squared(mesh, spin, sparse_lc, c_lambert=0.1):
    """Compute chi-squared contribution from sparse data.

    Sparse data points are treated as absolute brightness measurements
    (no per-lightcurve scaling). A single global scaling factor is fitted.

    Parameters
    ----------
    mesh : TriMesh
        Shape model.
    spin : SpinState
        Spin state.
    sparse_lc : LightcurveData
        Sparse observations packed into LightcurveData.
    c_lambert : float
        Lambert weight.

    Returns
    -------
    chi2 : float
        Chi-squared for sparse data.
    n_pts : int
        Number of sparse points.
    """
    sun_body, obs_body = _precompute_body_dirs(spin, sparse_lc)
    model = generate_lightcurve_direct(mesh, sun_body, obs_body, c_lambert)

    if np.all(model == 0):
        return 1e10, len(sparse_lc.jd)

    # Fit global scaling factor
    w = sparse_lc.weights
    obs = sparse_lc.brightness
    c_fit = np.sum(w * obs * model) / (np.sum(w * model ** 2) + 1e-30)
    residuals = obs - c_fit * model
    chi2 = np.sum(w * residuals ** 2)
    n_pts = len(sparse_lc.jd)

    return chi2, n_pts


def combined_chi_squared(mesh, spin, dense_lcs, sparse_lc,
                         c_lambert=0.1, lambda_sparse=1.0, reg_weight=0.0):
    """Combined objective function weighting dense and sparse contributions.

    chi2_total = chi2_dense + lambda_sparse * chi2_sparse + regularization

    The dense and sparse chi-squared values are each normalized by their
    respective number of data points before combination.

    Parameters
    ----------
    mesh : TriMesh
        Shape model.
    spin : SpinState
        Spin state.
    dense_lcs : list of LightcurveData
        Dense (ground-based) lightcurves.
    sparse_lc : LightcurveData or None
        Sparse observations. If None, only dense chi-squared is returned.
    c_lambert : float
        Lambert weight.
    lambda_sparse : float
        Relative weight of sparse data in the objective (default 1.0).
    reg_weight : float
        Regularization weight for area smoothness.

    Returns
    -------
    chi2_total : float
        Combined chi-squared.
    """
    # Dense contribution (already normalized per data point internally)
    chi2_dense = 0.0
    n_dense = 0
    if dense_lcs:
        for lc in dense_lcs:
            sun_body, obs_body = _precompute_body_dirs(spin, lc)
            model = generate_lightcurve_direct(mesh, sun_body, obs_body, c_lambert)
            if np.all(model == 0):
                chi2_dense += 1e10
                continue
            w = lc.weights
            c_fit = np.sum(w * lc.brightness * model) / (
                np.sum(w * model ** 2) + 1e-30)
            residuals = lc.brightness - c_fit * model
            chi2_dense += np.sum(w * residuals ** 2)
            n_dense += len(lc.jd)

    if n_dense > 0:
        chi2_dense /= n_dense

    # Sparse contribution
    chi2_sparse = 0.0
    if sparse_lc is not None and len(sparse_lc.jd) > 0:
        sp_chi2, n_sparse = sparse_chi_squared(mesh, spin, sparse_lc, c_lambert)
        if n_sparse > 0:
            chi2_sparse = sp_chi2 / n_sparse

    # Regularization
    reg = 0.0
    if reg_weight > 0:
        mean_area = np.mean(mesh.areas)
        reg = reg_weight * np.sum(
            (mesh.areas - mean_area) ** 2) / (mean_area ** 2 + 1e-30)

    chi2_total = chi2_dense + lambda_sparse * chi2_sparse + reg
    return chi2_total


# ---------------------------------------------------------------------------
# Combined inversion: optimize shape using dense + sparse
# ---------------------------------------------------------------------------

def optimize_combined(initial_mesh, spin, dense_lcs, sparse_lc,
                      c_lambert=0.1, lambda_sparse=1.0, reg_weight=0.01,
                      max_iter=200, verbose=False):
    """Optimize facet areas using combined dense + sparse objective.

    Parameters
    ----------
    initial_mesh : TriMesh
        Starting shape (e.g., sphere).
    spin : SpinState
        Fixed spin state.
    dense_lcs : list of LightcurveData
        Dense lightcurves.
    sparse_lc : LightcurveData or None
        Sparse observations.
    c_lambert : float
    lambda_sparse : float
    reg_weight : float
    max_iter : int
    verbose : bool

    Returns
    -------
    optimized_mesh : TriMesh
        Shape with optimized facet areas.
    chi2_final : float
        Final combined chi-squared.
    history : list of float
        Chi-squared history.
    """
    from scipy.optimize import minimize as sp_minimize

    normals = initial_mesh.normals.copy()
    faces = initial_mesh.faces.copy()
    vertices = initial_mesh.vertices.copy()

    # Pre-compute body directions for dense lightcurves
    dense_precomputed = [_precompute_body_dirs(spin, lc) for lc in dense_lcs]

    # Pre-compute body directions for sparse
    sparse_body_dirs = None
    if sparse_lc is not None and len(sparse_lc.jd) > 0:
        sparse_body_dirs = _precompute_body_dirs(spin, sparse_lc)

    log_areas0 = np.log(initial_mesh.areas + 1e-30)
    history = []

    def objective(log_areas):
        areas = np.exp(log_areas)
        mesh = TriMesh(vertices=vertices, faces=faces,
                       normals=normals, areas=areas)

        # Dense chi-squared
        chi2_d = 0.0
        n_d = 0
        for idx, lc in enumerate(dense_lcs):
            sb, ob = dense_precomputed[idx]
            model = generate_lightcurve_direct(mesh, sb, ob, c_lambert)
            if np.all(model == 0):
                chi2_d += 1e10
                continue
            w = lc.weights
            c_fit = np.sum(w * lc.brightness * model) / (
                np.sum(w * model ** 2) + 1e-30)
            residuals = lc.brightness - c_fit * model
            chi2_d += np.sum(w * residuals ** 2)
            n_d += len(lc.jd)
        if n_d > 0:
            chi2_d /= n_d

        # Sparse chi-squared
        chi2_s = 0.0
        if sparse_body_dirs is not None:
            sb, ob = sparse_body_dirs
            model = generate_lightcurve_direct(mesh, sb, ob, c_lambert)
            if not np.all(model == 0):
                w = sparse_lc.weights
                c_fit = np.sum(w * sparse_lc.brightness * model) / (
                    np.sum(w * model ** 2) + 1e-30)
                residuals = sparse_lc.brightness - c_fit * model
                chi2_s = np.sum(w * residuals ** 2) / len(sparse_lc.jd)

        # Regularization
        reg = 0.0
        if reg_weight > 0:
            mean_a = np.mean(areas)
            reg = reg_weight * np.sum(
                (areas - mean_a) ** 2) / (mean_a ** 2 + 1e-30)

        total = chi2_d + lambda_sparse * chi2_s + reg
        history.append(total)
        return total

    result = sp_minimize(objective, log_areas0, method='L-BFGS-B',
                         options={'maxiter': max_iter, 'ftol': 1e-12})

    areas_opt = np.exp(result.x)
    optimized_mesh = TriMesh(vertices=vertices, faces=faces,
                             normals=normals, areas=areas_opt)
    chi2_final = result.fun

    if verbose:
        print(f"  Combined optimization: chi2={chi2_final:.6f}, "
              f"iterations={result.nit}, success={result.success}")

    return optimized_mesh, chi2_final, history
