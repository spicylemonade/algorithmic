"""
Benchmark Suite Assembly Script

Sets up the ground truth validation benchmark for >= 5 asteroids.
Attempts to download real DAMIT shapes; falls back to synthetic ellipsoid
models with known parameters from published literature.

Generates:
- results/ground_truth/<name>.obj — ground truth mesh
- results/ground_truth/<name>_spin.json — spin parameters
- results/observations/<name>_dense_lc_*.csv — synthetic dense lightcurves
- results/observations/<name>_sparse.csv — synthetic sparse observations
- benchmark_manifest.json — metadata manifest

References:
    DAMIT database (Durech et al. 2010)
    ALCDEF (Warner et al. 2009)
"""

import os
import json
import numpy as np

from data_ingestion import (VALIDATION_TARGETS, setup_validation_targets,
                            generate_synthetic_lightcurves)
from geometry import SpinState, OrbitalElements, compute_geometry
from forward_model import (save_obj, generate_lightcurve_direct,
                           create_sphere_mesh)


# Orbital elements (approximate, for synthetic data generation)
ORBITAL_PARAMS = {
    "Eros": OrbitalElements(a=1.458, e=0.223, i=np.radians(10.83),
                             node=np.radians(304.4), peri=np.radians(178.9),
                             M0=np.radians(190.0), epoch=2451545.0),
    "Itokawa": OrbitalElements(a=1.324, e=0.280, i=np.radians(1.62),
                                node=np.radians(69.1), peri=np.radians(162.8),
                                M0=np.radians(40.0), epoch=2451545.0),
    "Kleopatra": OrbitalElements(a=2.795, e=0.253, i=np.radians(13.11),
                                  node=np.radians(215.7), peri=np.radians(179.6),
                                  M0=np.radians(100.0), epoch=2451545.0),
    "Gaspra": OrbitalElements(a=2.210, e=0.174, i=np.radians(4.10),
                               node=np.radians(253.2), peri=np.radians(132.8),
                               M0=np.radians(60.0), epoch=2451545.0),
    "Betulia": OrbitalElements(a=2.196, e=0.487, i=np.radians(52.12),
                                node=np.radians(62.3), peri=np.radians(159.6),
                                M0=np.radians(250.0), epoch=2451545.0),
}


def generate_dense_lightcurves_from_orbit(shape_model, orbital_elements,
                                           n_lightcurves=5, n_points=60,
                                           c_lambert=0.1, seed=42):
    """Generate synthetic dense lightcurves using orbital geometry."""
    rng = np.random.default_rng(seed)
    spin = shape_model.spin

    # Generate observations at different orbital phases
    orbital_period = 365.25 * shape_model.spin.period_hours  # rough
    lightcurve_data = []

    for i in range(n_lightcurves):
        # Pick a random epoch in the orbit
        base_jd = orbital_elements.epoch + rng.uniform(0, 365.25 * 2)
        period_days = spin.period_hours / 24.0

        # One rotation of dense data
        phases = np.linspace(0, 360, n_points, endpoint=False)
        jd_array = base_jd + phases / 360.0 * period_days

        # Compute geometry
        geo = compute_geometry(orbital_elements, spin, jd_array)

        # Compute brightness
        brightness = generate_lightcurve_direct(
            shape_model.mesh, geo['sun_body'], geo['obs_body'], c_lambert
        )

        # Add noise
        noise_level = 0.005
        noise = rng.normal(0, noise_level * np.mean(brightness), len(brightness))
        brightness_noisy = brightness + noise

        # Convert to magnitudes
        mags = -2.5 * np.log10(np.maximum(brightness_noisy, 1e-30))
        mags -= np.mean(mags)

        lc_data = {
            "jd": jd_array.tolist(),
            "mag": mags.tolist(),
            "mag_err": [0.005] * len(mags),
            "brightness": brightness_noisy.tolist(),
            "phase_angle_deg": np.degrees(geo['phase_angle']).tolist(),
            "r_helio": geo['r_helio'].tolist(),
            "r_geo": geo['r_geo'].tolist(),
        }
        lightcurve_data.append(lc_data)

    return lightcurve_data


def generate_sparse_observations(shape_model, orbital_elements,
                                  n_points=200, n_apparitions=6,
                                  c_lambert=0.1, seed=42):
    """Generate synthetic sparse observations across multiple apparitions."""
    rng = np.random.default_rng(seed)
    spin = shape_model.spin

    orbital_period_days = 365.25 * (orbital_elements.a ** 1.5)
    app_spacing = orbital_period_days / n_apparitions
    pts_per_app = n_points // n_apparitions

    jd_list = []
    for app in range(n_apparitions):
        base_jd = orbital_elements.epoch + app * app_spacing
        n_this = pts_per_app if app < n_apparitions - 1 else n_points - len(jd_list)
        jds = base_jd + rng.uniform(0, 30, n_this)
        jd_list.extend(sorted(jds.tolist()))

    jd_array = np.array(sorted(jd_list))
    geo = compute_geometry(orbital_elements, spin, jd_array)
    brightness = generate_lightcurve_direct(
        shape_model.mesh, geo['sun_body'], geo['obs_body'], c_lambert
    )

    noise_level = 0.003
    noise = rng.normal(0, noise_level * np.mean(brightness), len(brightness))
    brightness_noisy = brightness + noise

    mags = -2.5 * np.log10(np.maximum(brightness_noisy, 1e-30))

    observations = []
    for j in range(len(jd_array)):
        observations.append({
            "jd": jd_array[j],
            "mag": mags[j],
            "mag_err": 0.003,
            "phase_angle_deg": float(np.degrees(geo['phase_angle'][j])),
            "r_helio": float(geo['r_helio'][j]),
            "r_geo": float(geo['r_geo'][j]),
        })

    return observations


def setup_benchmark(output_dir="results", try_download=False):
    """Set up the full validation benchmark suite.

    Parameters
    ----------
    output_dir : str
        Base output directory.
    try_download : bool
        Attempt to download from DAMIT.

    Returns
    -------
    dict
        Benchmark manifest.
    """
    gt_dir = os.path.join(output_dir, "ground_truth")
    obs_dir = os.path.join(output_dir, "observations")
    os.makedirs(gt_dir, exist_ok=True)
    os.makedirs(obs_dir, exist_ok=True)

    # Set up ground truth shapes
    targets = setup_validation_targets(output_dir=gt_dir,
                                        try_download=try_download)

    manifest = {
        "version": "1.0",
        "n_targets": len(targets),
        "targets": {}
    }

    for name, model in targets.items():
        print(f"\nGenerating benchmark data for {name}...")

        params = VALIDATION_TARGETS[name]
        orbital = ORBITAL_PARAMS.get(name)

        target_info = {
            "id": params["id"],
            "name": name,
            "ground_truth_obj": os.path.join("ground_truth", f"{name.lower()}.obj"),
            "spin": {
                "lambda_deg": params["pole_lambda"],
                "beta_deg": params["pole_beta"],
                "period_hours": params["period_hours"],
                "jd0": 2451545.0,
            },
            "axes_km": list(params["axes"]),
            "n_vertices": int(len(model.mesh.vertices)),
            "n_faces": int(len(model.mesh.faces)),
            "source": model.source,
        }

        # Generate dense lightcurves
        if orbital is not None:
            dense_lcs = generate_dense_lightcurves_from_orbit(
                model, orbital, n_lightcurves=5, n_points=60, seed=42
            )
            dense_files = []
            for i, lc in enumerate(dense_lcs):
                fname = f"{name.lower()}_dense_lc_{i:02d}.json"
                fpath = os.path.join(obs_dir, fname)
                with open(fpath, 'w') as f:
                    json.dump(lc, f, indent=2)
                dense_files.append(os.path.join("observations", fname))
            target_info["dense_lightcurves"] = dense_files
            target_info["n_dense_lc"] = len(dense_files)

            # Generate sparse observations
            sparse_obs = generate_sparse_observations(
                model, orbital, n_points=200, n_apparitions=6, seed=42
            )
            sparse_fname = f"{name.lower()}_sparse.json"
            sparse_fpath = os.path.join(obs_dir, sparse_fname)
            with open(sparse_fpath, 'w') as f:
                json.dump(sparse_obs, f, indent=2)
            target_info["sparse_observations"] = os.path.join("observations",
                                                               sparse_fname)
            target_info["n_sparse_obs"] = len(sparse_obs)
        else:
            target_info["dense_lightcurves"] = []
            target_info["n_dense_lc"] = 0
            target_info["sparse_observations"] = None
            target_info["n_sparse_obs"] = 0

        manifest["targets"][name] = target_info
        print(f"  {name}: {target_info['n_faces']} faces, "
              f"{target_info['n_dense_lc']} dense LC, "
              f"{target_info['n_sparse_obs']} sparse obs")

    # Save manifest
    manifest_path = os.path.join(output_dir, "benchmark_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"\nBenchmark manifest saved to {manifest_path}")

    return manifest


if __name__ == '__main__':
    np.random.seed(42)
    manifest = setup_benchmark(output_dir="results", try_download=False)
    print(f"\n{'='*60}")
    print(f"Benchmark suite assembled: {manifest['n_targets']} targets")
    print(f"{'='*60}")
