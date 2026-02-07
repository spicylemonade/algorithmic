"""
Data Ingestion Layer (Module 6)

Downloads, parses, and standardizes photometric data from ALCDEF and DAMIT,
and ground truth shape models for validation.

References:
    Durech et al. (2010) — DAMIT database
    Warner et al. (2009) — LCDB / ALCDEF
"""

import os
import re
import json
import numpy as np
import requests
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple
from forward_model import TriMesh, load_obj, compute_face_properties
from geometry import SpinState, OrbitalElements


# ─── Data classes ────────────────────────────────────────────────────────────

@dataclass
class PhotometryPoint:
    """Single photometric observation."""
    jd: float
    mag: float
    mag_err: float = 0.0
    filter_name: str = "V"


@dataclass
class DenseLightcurve:
    """Dense time-series lightcurve for one observing session."""
    asteroid_name: str
    points: List[PhotometryPoint]
    observer: str = ""
    reference: str = ""

    @property
    def jd_array(self):
        return np.array([p.jd for p in self.points])

    @property
    def mag_array(self):
        return np.array([p.mag for p in self.points])

    @property
    def err_array(self):
        return np.array([p.mag_err for p in self.points])


@dataclass
class ShapeModel:
    """Asteroid shape model with spin parameters."""
    asteroid_id: int
    asteroid_name: str
    mesh: TriMesh
    spin: SpinState
    source: str = "DAMIT"


@dataclass
class AsteroidData:
    """Aggregated data for one asteroid."""
    designation: str
    name: str
    dense_lightcurves: List[DenseLightcurve] = field(default_factory=list)
    sparse_photometry: List[PhotometryPoint] = field(default_factory=list)
    shape_model: Optional[ShapeModel] = None
    orbital_elements: Optional[OrbitalElements] = None


# ─── ALCDEF Parsing ──────────────────────────────────────────────────────────

def parse_alcdef_string(content):
    """Parse ALCDEF-format data from a string.

    ALCDEF format uses keyword=value pairs. Each observing session is
    delimited by STARTMETADATA/ENDMETADATA and STARTDATA/ENDDATA blocks.

    Parameters
    ----------
    content : str
        ALCDEF file content.

    Returns
    -------
    list of DenseLightcurve
        Parsed lightcurves.
    """
    lightcurves = []
    lines = content.split('\n')

    current_name = ""
    current_observer = ""
    current_points = []
    in_data = False
    filter_name = "V"

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Check for bare keywords first (no '=' sign)
        upper_line = line.upper()
        if upper_line == 'STARTDATA':
            in_data = True
            current_points = []
            continue
        elif upper_line == 'ENDDATA':
            in_data = False
            if current_points:
                lc = DenseLightcurve(
                    asteroid_name=current_name,
                    points=current_points.copy(),
                    observer=current_observer
                )
                lightcurves.append(lc)
            current_points = []
            continue
        elif upper_line in ('STARTMETADATA', 'ENDMETADATA'):
            continue

        if '=' in line:
            key, _, value = line.partition('=')
            key = key.strip().upper()
            value = value.strip()

            if key == 'OBJECTNUMBER' or key == 'OBJECTNAME':
                current_name = value
            elif key == 'OBSERVERS':
                current_observer = value
            elif key == 'FILTER':
                filter_name = value if value else "V"

        elif in_data:
            # Data line: JD|MAG|MAGERR (pipe-delimited)
            parts = line.split('|')
            if len(parts) >= 2:
                try:
                    jd = float(parts[0].strip())
                    mag = float(parts[1].strip())
                    mag_err = float(parts[2].strip()) if len(parts) > 2 else 0.01
                    current_points.append(PhotometryPoint(
                        jd=jd, mag=mag, mag_err=mag_err, filter_name=filter_name
                    ))
                except ValueError:
                    continue

    return lightcurves


def parse_alcdef_file(filepath):
    """Parse an ALCDEF file from disk.

    Parameters
    ----------
    filepath : str
        Path to ALCDEF file.

    Returns
    -------
    list of DenseLightcurve
    """
    with open(filepath, 'r') as f:
        content = f.read()
    return parse_alcdef_string(content)


def fetch_alcdef_data(asteroid_designation, output_dir="results/observations"):
    """Attempt to download ALCDEF data for an asteroid.

    Parameters
    ----------
    asteroid_designation : str
        Asteroid number or name (e.g., "433" or "Eros").
    output_dir : str
        Directory to save downloaded files.

    Returns
    -------
    list of DenseLightcurve or None
        Parsed lightcurves, or None if download fails.
    """
    os.makedirs(output_dir, exist_ok=True)
    url = f"https://alcdef.org/PHP/alcdef_GenerateALCDEFPage.php?AstInfo={asteroid_designation}"

    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200 and len(response.text) > 100:
            filepath = os.path.join(output_dir, f"alcdef_{asteroid_designation}.txt")
            with open(filepath, 'w') as f:
                f.write(response.text)
            return parse_alcdef_string(response.text)
        else:
            print(f"  ALCDEF: no data for {asteroid_designation} (status {response.status_code})")
            return None
    except (requests.RequestException, ConnectionError) as e:
        print(f"  ALCDEF download failed for {asteroid_designation}: {e}")
        return None


# ─── DAMIT Parsing ───────────────────────────────────────────────────────────

def parse_damit_shape(obj_content):
    """Parse a DAMIT shape model from OBJ-format string.

    Parameters
    ----------
    obj_content : str
        OBJ file content.

    Returns
    -------
    TriMesh
        Parsed mesh.
    """
    vertices = []
    faces = []
    for line in obj_content.split('\n'):
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] == 'v' and len(parts) >= 4:
            vertices.append([float(x) for x in parts[1:4]])
        elif parts[0] == 'f':
            face_verts = []
            for p in parts[1:]:
                idx = int(p.split('/')[0]) - 1
                face_verts.append(idx)
            for k in range(1, len(face_verts) - 1):
                faces.append([face_verts[0], face_verts[k], face_verts[k+1]])

    vertices = np.array(vertices, dtype=np.float64)
    faces = np.array(faces, dtype=np.int64)
    normals, areas = compute_face_properties(vertices, faces)
    return TriMesh(vertices=vertices, faces=faces, normals=normals, areas=areas)


def parse_damit_spin(spin_content):
    """Parse DAMIT spin parameters.

    Typical format:
    lambda  beta  P  JD0
    (may have additional lines with different formats)

    Parameters
    ----------
    spin_content : str
        Spin parameter file content.

    Returns
    -------
    SpinState
    """
    lines = [l.strip() for l in spin_content.strip().split('\n') if l.strip() and not l.startswith('#')]
    if not lines:
        raise ValueError("Empty spin parameter content")

    # Try to parse first non-empty line
    parts = lines[0].split()
    if len(parts) >= 4:
        lam = float(parts[0])
        beta = float(parts[1])
        period = float(parts[2])
        jd0 = float(parts[3])
    elif len(parts) >= 3:
        lam = float(parts[0])
        beta = float(parts[1])
        period = float(parts[2])
        jd0 = 2451545.0  # default J2000.0
    else:
        raise ValueError(f"Cannot parse spin parameters: {lines[0]}")

    return SpinState(lambda_deg=lam, beta_deg=beta, period_hours=period, jd0=jd0)


def fetch_damit_model(asteroid_id, output_dir="results/ground_truth"):
    """Attempt to download a DAMIT shape model and spin parameters.

    Parameters
    ----------
    asteroid_id : int
        Asteroid number in DAMIT.
    output_dir : str
        Directory to save downloaded files.

    Returns
    -------
    ShapeModel or None
        Parsed shape model, or None if download fails.
    """
    os.makedirs(output_dir, exist_ok=True)

    # DAMIT model download URL patterns
    base_url = "https://astro.troja.mff.cuni.cz/projects/damit"
    obj_url = f"{base_url}/asteroid_models/view_obj/{asteroid_id}"
    spin_url = f"{base_url}/asteroid_models/view_spin/{asteroid_id}"

    try:
        # Download shape
        resp_obj = requests.get(obj_url, timeout=30)
        if resp_obj.status_code != 200 or len(resp_obj.text) < 50:
            print(f"  DAMIT: shape not found for asteroid {asteroid_id}")
            return None

        # Download spin
        resp_spin = requests.get(spin_url, timeout=30)

        # Save files
        obj_path = os.path.join(output_dir, f"damit_{asteroid_id}.obj")
        with open(obj_path, 'w') as f:
            f.write(resp_obj.text)

        mesh = parse_damit_shape(resp_obj.text)

        if resp_spin.status_code == 200 and len(resp_spin.text) > 5:
            spin_path = os.path.join(output_dir, f"damit_{asteroid_id}_spin.txt")
            with open(spin_path, 'w') as f:
                f.write(resp_spin.text)
            spin = parse_damit_spin(resp_spin.text)
        else:
            spin = SpinState(lambda_deg=0, beta_deg=0, period_hours=0, jd0=2451545.0)

        return ShapeModel(
            asteroid_id=asteroid_id,
            asteroid_name=str(asteroid_id),
            mesh=mesh,
            spin=spin,
            source="DAMIT"
        )

    except (requests.RequestException, ConnectionError) as e:
        print(f"  DAMIT download failed for asteroid {asteroid_id}: {e}")
        return None


# ─── Synthetic / Fallback Data Generation ────────────────────────────────────

def generate_synthetic_validation_target(name, asteroid_id, a_axis, b_axis, c_axis,
                                         pole_lambda, pole_beta, period_hours,
                                         output_dir="results/ground_truth"):
    """Generate synthetic ground truth data for validation when real data is unavailable.

    Parameters
    ----------
    name : str
        Asteroid name.
    asteroid_id : int
        Asteroid number.
    a_axis, b_axis, c_axis : float
        Ellipsoid semi-axes.
    pole_lambda, pole_beta : float
        Pole direction in degrees.
    period_hours : float
        Sidereal rotation period.
    output_dir : str
        Output directory for .obj file.

    Returns
    -------
    ShapeModel
        Synthetic shape model.
    """
    from forward_model import create_ellipsoid_mesh, save_obj

    os.makedirs(output_dir, exist_ok=True)
    mesh = create_ellipsoid_mesh(a_axis, b_axis, c_axis, n_subdivisions=3)
    spin = SpinState(lambda_deg=pole_lambda, beta_deg=pole_beta,
                     period_hours=period_hours, jd0=2451545.0)

    obj_path = os.path.join(output_dir, f"{name.lower()}.obj")
    save_obj(obj_path, mesh)

    spin_data = {
        "lambda_deg": pole_lambda, "beta_deg": pole_beta,
        "period_hours": period_hours, "jd0": 2451545.0
    }
    spin_path = os.path.join(output_dir, f"{name.lower()}_spin.json")
    with open(spin_path, 'w') as f:
        json.dump(spin_data, f, indent=2)

    return ShapeModel(
        asteroid_id=asteroid_id,
        asteroid_name=name,
        mesh=mesh,
        spin=spin,
        source="synthetic"
    )


def generate_synthetic_lightcurves(shape_model, n_lightcurves=5, n_points_per_lc=60,
                                   c_lambert=0.1):
    """Generate synthetic dense lightcurves for a shape model.

    Parameters
    ----------
    shape_model : ShapeModel
        Ground truth shape model.
    n_lightcurves : int
        Number of lightcurves at different geometries.
    n_points_per_lc : int
        Points per lightcurve.
    c_lambert : float
        Lambert weight.

    Returns
    -------
    list of DenseLightcurve
    """
    from forward_model import generate_rotation_lightcurve

    np.random.seed(42)
    lightcurves = []

    for i in range(n_lightcurves):
        # Random viewing geometry
        sun_ecl = np.random.randn(3)
        sun_ecl /= np.linalg.norm(sun_ecl)
        obs_ecl = sun_ecl + 0.1 * np.random.randn(3)
        obs_ecl /= np.linalg.norm(obs_ecl)

        phases, brightness = generate_rotation_lightcurve(
            shape_model.mesh, shape_model.spin, sun_ecl, obs_ecl,
            n_points=n_points_per_lc, c_lambert=c_lambert
        )

        # Convert to magnitudes
        mags = -2.5 * np.log10(np.maximum(brightness, 1e-30))
        mags -= np.mean(mags)

        period_days = shape_model.spin.period_hours / 24.0
        jd_array = shape_model.spin.jd0 + phases / 360.0 * period_days

        # Add small noise
        noise = np.random.normal(0, 0.005, len(mags))
        mags += noise

        points = [PhotometryPoint(jd=jd_array[j], mag=mags[j], mag_err=0.005)
                  for j in range(len(mags))]

        lc = DenseLightcurve(
            asteroid_name=shape_model.asteroid_name,
            points=points,
            observer="synthetic"
        )
        lightcurves.append(lc)

    return lightcurves


# ─── Validation Targets Setup ────────────────────────────────────────────────

# Known parameters for validation asteroids (from literature)
VALIDATION_TARGETS = {
    "Eros": {
        "id": 433,
        "axes": (17.0, 5.5, 5.5),  # km, approximate
        "pole_lambda": 11.4,
        "pole_beta": 17.2,
        "period_hours": 5.270,
    },
    "Itokawa": {
        "id": 25143,
        "axes": (0.535, 0.294, 0.209),  # km
        "pole_lambda": 128.5,
        "pole_beta": -89.66,
        "period_hours": 12.132,
    },
    "Kleopatra": {
        "id": 216,
        "axes": (135.0, 58.0, 50.0),  # km, very elongated
        "pole_lambda": 73.0,
        "pole_beta": 21.0,
        "period_hours": 5.385,
    },
    "Gaspra": {
        "id": 951,
        "axes": (9.1, 5.2, 4.4),  # km
        "pole_lambda": 9.5,
        "pole_beta": 26.7,
        "period_hours": 7.042,
    },
    "Betulia": {
        "id": 1580,
        "axes": (3.2, 2.8, 2.4),  # km, approximate
        "pole_lambda": 136.0,
        "pole_beta": 22.0,
        "period_hours": 6.138,
    },
}


def setup_validation_targets(output_dir="results/ground_truth", try_download=True):
    """Set up validation targets, downloading real data if possible,
    falling back to synthetic data.

    Parameters
    ----------
    output_dir : str
    try_download : bool
        If True, attempt to download from DAMIT first.

    Returns
    -------
    dict of str -> ShapeModel
        Validation targets keyed by name.
    """
    targets = {}

    for name, params in VALIDATION_TARGETS.items():
        print(f"Setting up {name} (#{params['id']})...")

        shape_model = None
        if try_download:
            shape_model = fetch_damit_model(params['id'], output_dir)

        if shape_model is None:
            print(f"  Using synthetic data for {name}")
            shape_model = generate_synthetic_validation_target(
                name=name,
                asteroid_id=params['id'],
                a_axis=params['axes'][0],
                b_axis=params['axes'][1],
                c_axis=params['axes'][2],
                pole_lambda=params['pole_lambda'],
                pole_beta=params['pole_beta'],
                period_hours=params['period_hours'],
                output_dir=output_dir
            )

        targets[name] = shape_model

    return targets
