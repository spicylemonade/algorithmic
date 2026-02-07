"""
Viewing Geometry Calculator (Module 8)

Computes Sun-asteroid-observer geometry at arbitrary epochs from orbital
elements. Provides phase angle, aspect angle, solar elongation, and
direction vectors in the asteroid body frame.

References:
    Kaasalainen & Torppa (2001), Kaasalainen et al. (2001)
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

# Gravitational parameter of the Sun in AU^3 / day^2
GM_SUN = 2.9591220828559093e-4

# Speed of light in AU/day
C_LIGHT = 173.14463267424034


@dataclass
class OrbitalElements:
    """Osculating Keplerian orbital elements."""
    a: float       # semi-major axis (AU)
    e: float       # eccentricity
    i: float       # inclination (radians)
    node: float    # longitude of ascending node (radians)
    peri: float    # argument of perihelion (radians)
    M0: float      # mean anomaly at epoch (radians)
    epoch: float   # reference epoch (JD)


@dataclass
class SpinState:
    """Asteroid spin state parameters."""
    lambda_deg: float   # pole ecliptic longitude (degrees)
    beta_deg: float     # pole ecliptic latitude (degrees)
    period_hours: float # sidereal rotation period (hours)
    jd0: float          # reference epoch (JD)
    phi0: float = 0.0   # initial rotational phase (radians)


def solve_kepler(M, e, tol=1e-12, max_iter=50):
    """Solve Kepler's equation M = E - e*sin(E) for eccentric anomaly E.

    Parameters
    ----------
    M : float or np.ndarray
        Mean anomaly (radians).
    e : float
        Eccentricity.
    tol : float
        Convergence tolerance.
    max_iter : int
        Maximum Newton-Raphson iterations.

    Returns
    -------
    E : float or np.ndarray
        Eccentric anomaly (radians).
    """
    M = np.asarray(M, dtype=np.float64)
    E = M.copy()
    for _ in range(max_iter):
        dE = (M - E + e * np.sin(E)) / (1.0 - e * np.cos(E))
        E += dE
        if np.all(np.abs(dE) < tol):
            break
    return E


def orbital_position(elements, jd):
    """Compute heliocentric ecliptic Cartesian position from orbital elements.

    Parameters
    ----------
    elements : OrbitalElements
        Keplerian orbital elements.
    jd : float or np.ndarray
        Julian Date(s).

    Returns
    -------
    pos : np.ndarray, shape (..., 3)
        Heliocentric ecliptic XYZ position in AU.
    """
    jd = np.asarray(jd, dtype=np.float64)
    n = np.sqrt(GM_SUN / elements.a**3)  # mean motion (rad/day)
    M = elements.M0 + n * (jd - elements.epoch)
    E = solve_kepler(M, elements.e)

    # True anomaly
    nu = 2.0 * np.arctan2(
        np.sqrt(1 + elements.e) * np.sin(E / 2),
        np.sqrt(1 - elements.e) * np.cos(E / 2)
    )

    # Heliocentric distance
    r = elements.a * (1 - elements.e * np.cos(E))

    # Position in orbital plane
    x_orb = r * np.cos(nu)
    y_orb = r * np.sin(nu)

    # Rotation matrices
    cos_O, sin_O = np.cos(elements.node), np.sin(elements.node)
    cos_i, sin_i = np.cos(elements.i), np.sin(elements.i)
    cos_w, sin_w = np.cos(elements.peri), np.sin(elements.peri)

    # Combined rotation to ecliptic frame
    Px = (cos_O * cos_w - sin_O * sin_w * cos_i)
    Py = (sin_O * cos_w + cos_O * sin_w * cos_i)
    Pz = sin_w * sin_i

    Qx = (-cos_O * sin_w - sin_O * cos_w * cos_i)
    Qy = (-sin_O * sin_w + cos_O * cos_w * cos_i)
    Qz = cos_w * sin_i

    x = Px * x_orb + Qx * y_orb
    y = Py * x_orb + Qy * y_orb
    z = Pz * x_orb + Qz * y_orb

    return np.stack([x, y, z], axis=-1)


def earth_position_approx(jd):
    """Approximate Earth heliocentric ecliptic position (circular orbit).

    Parameters
    ----------
    jd : float or np.ndarray
        Julian Date(s).

    Returns
    -------
    pos : np.ndarray, shape (..., 3)
        Heliocentric ecliptic XYZ position in AU.
    """
    jd = np.asarray(jd, dtype=np.float64)
    # J2000.0 epoch
    T = (jd - 2451545.0) / 365.25
    # Mean longitude of Earth (approximate)
    L = np.radians(100.46 + 360.0 * T) % (2 * np.pi)
    x = np.cos(L)
    y = np.sin(L)
    z = np.zeros_like(x)
    return np.stack([x, y, z], axis=-1)


def rotation_matrix_z(angle):
    """Rotation matrix about z-axis."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def rotation_matrix_y(angle):
    """Rotation matrix about y-axis."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def spin_axis_vector(lambda_deg, beta_deg):
    """Compute spin axis unit vector in ecliptic coordinates.

    Parameters
    ----------
    lambda_deg : float
        Pole ecliptic longitude (degrees).
    beta_deg : float
        Pole ecliptic latitude (degrees).

    Returns
    -------
    z_spin : np.ndarray, shape (3,)
        Spin axis unit vector.
    """
    lam = np.radians(lambda_deg)
    bet = np.radians(beta_deg)
    return np.array([np.cos(bet) * np.cos(lam),
                     np.cos(bet) * np.sin(lam),
                     np.sin(bet)])


def ecliptic_to_body_matrix(spin, jd):
    """Compute rotation matrix from ecliptic to body frame at given epoch.

    Parameters
    ----------
    spin : SpinState
        Spin state parameters.
    jd : float
        Julian Date.

    Returns
    -------
    R : np.ndarray, shape (3, 3)
        Rotation matrix.
    """
    lam = np.radians(spin.lambda_deg)
    bet = np.radians(spin.beta_deg)
    period_days = spin.period_hours / 24.0
    phi = spin.phi0 + 2.0 * np.pi / period_days * (jd - spin.jd0)

    R = rotation_matrix_z(phi) @ rotation_matrix_y(np.pi / 2 - bet) @ rotation_matrix_z(-lam)
    return R


def compute_geometry(ast_elements, spin, jd_array, earth_pos=None):
    """Compute viewing geometry for a set of epochs.

    Parameters
    ----------
    ast_elements : OrbitalElements
        Asteroid orbital elements.
    spin : SpinState
        Asteroid spin state.
    jd_array : np.ndarray
        Array of Julian Dates.
    earth_pos : np.ndarray, optional
        Earth positions, shape (N, 3). If None, uses approximate circular orbit.

    Returns
    -------
    dict with keys:
        'sun_body' : np.ndarray, shape (N, 3) — Sun direction in body frame
        'obs_body' : np.ndarray, shape (N, 3) — Observer direction in body frame
        'phase_angle' : np.ndarray, shape (N,) — Phase angle in radians
        'aspect_angle' : np.ndarray, shape (N,) — Aspect angle in radians
        'r_helio' : np.ndarray, shape (N,) — Heliocentric distance (AU)
        'r_geo' : np.ndarray, shape (N,) — Geocentric distance (AU)
    """
    jd_array = np.asarray(jd_array, dtype=np.float64)
    N = len(jd_array)

    # Asteroid heliocentric position
    r_ast = orbital_position(ast_elements, jd_array)

    # Earth position
    if earth_pos is None:
        r_earth = earth_position_approx(jd_array)
    else:
        r_earth = np.asarray(earth_pos, dtype=np.float64)

    # Direction vectors in ecliptic frame
    sun_ecl = -r_ast / np.linalg.norm(r_ast, axis=-1, keepdims=True)
    obs_vec = r_earth - r_ast
    r_geo = np.linalg.norm(obs_vec, axis=-1)
    obs_ecl = obs_vec / r_geo[..., np.newaxis]

    # Phase angle
    cos_alpha = np.sum(sun_ecl * obs_ecl, axis=-1)
    cos_alpha = np.clip(cos_alpha, -1, 1)
    phase_angle = np.arccos(cos_alpha)

    # Aspect angle
    z_spin = spin_axis_vector(spin.lambda_deg, spin.beta_deg)
    cos_asp = np.dot(obs_ecl, z_spin)
    cos_asp = np.clip(cos_asp, -1, 1)
    aspect_angle = np.arccos(cos_asp)

    # Transform to body frame
    sun_body = np.zeros((N, 3))
    obs_body = np.zeros((N, 3))
    for j in range(N):
        R = ecliptic_to_body_matrix(spin, jd_array[j])
        sun_body[j] = R @ sun_ecl[j]
        obs_body[j] = R @ obs_ecl[j]

    r_helio = np.linalg.norm(r_ast, axis=-1)

    return {
        'sun_body': sun_body,
        'obs_body': obs_body,
        'phase_angle': phase_angle,
        'aspect_angle': aspect_angle,
        'r_helio': r_helio,
        'r_geo': r_geo,
    }
