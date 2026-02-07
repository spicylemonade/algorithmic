"""
Tests for data_ingestion.py

Validates ALCDEF parsing, DAMIT parsing, and synthetic data generation
for at least 3 validation targets.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import tempfile
from data_ingestion import (
    parse_alcdef_string, parse_damit_shape, parse_damit_spin,
    generate_synthetic_validation_target, generate_synthetic_lightcurves,
    setup_validation_targets, VALIDATION_TARGETS, PhotometryPoint,
    DenseLightcurve
)
from forward_model import save_obj

np.random.seed(42)


def test_parse_alcdef_string():
    """Test ALCDEF format parsing."""
    alcdef_content = """OBJECTNUMBER=433
OBJECTNAME=Eros
OBSERVERS=Test Observer
FILTER=V
STARTMETADATA
ENDMETADATA
STARTDATA
2451545.5|12.34|0.02
2451545.51|12.31|0.02
2451545.52|12.28|0.03
2451545.53|12.35|0.02
2451545.54|12.40|0.02
ENDDATA
OBJECTNUMBER=433
FILTER=R
STARTDATA
2451546.5|11.90|0.01
2451546.51|11.88|0.01
2451546.52|11.85|0.02
ENDDATA
"""
    lightcurves = parse_alcdef_string(alcdef_content)
    assert len(lightcurves) == 2, f"Expected 2 lightcurves, got {len(lightcurves)}"
    assert len(lightcurves[0].points) == 5, f"Expected 5 points, got {len(lightcurves[0].points)}"
    assert len(lightcurves[1].points) == 3, f"Expected 3 points, got {len(lightcurves[1].points)}"
    assert lightcurves[0].asteroid_name in ("433", "Eros")

    # Check parsed values
    assert abs(lightcurves[0].points[0].jd - 2451545.5) < 1e-10
    assert abs(lightcurves[0].points[0].mag - 12.34) < 1e-10
    assert abs(lightcurves[0].points[0].mag_err - 0.02) < 1e-10

    print("PASS: ALCDEF string parsing")


def test_parse_damit_shape():
    """Test DAMIT OBJ shape parsing."""
    obj_content = """# Simple tetrahedron
v 1.0 0.0 0.0
v 0.0 1.0 0.0
v 0.0 0.0 1.0
v 0.0 0.0 0.0
f 1 2 3
f 1 2 4
f 1 3 4
f 2 3 4
"""
    mesh = parse_damit_shape(obj_content)
    assert mesh.vertices.shape == (4, 3), f"Wrong vertex shape: {mesh.vertices.shape}"
    assert mesh.faces.shape == (4, 3), f"Wrong face shape: {mesh.faces.shape}"
    assert len(mesh.normals) == 4
    assert len(mesh.areas) == 4
    assert np.all(mesh.areas > 0)
    print("PASS: DAMIT shape parsing")


def test_parse_damit_spin():
    """Test DAMIT spin parameter parsing."""
    spin_content = "45.0 30.0 6.0 2451545.0"
    spin = parse_damit_spin(spin_content)
    assert abs(spin.lambda_deg - 45.0) < 1e-10
    assert abs(spin.beta_deg - 30.0) < 1e-10
    assert abs(spin.period_hours - 6.0) < 1e-10
    assert abs(spin.jd0 - 2451545.0) < 1e-10
    print("PASS: DAMIT spin parsing")


def test_synthetic_validation_targets():
    """Test synthetic validation target generation for >= 3 asteroids."""
    with tempfile.TemporaryDirectory() as tmpdir:
        targets = setup_validation_targets(output_dir=tmpdir, try_download=False)

        assert len(targets) >= 3, f"Expected >= 3 targets, got {len(targets)}"

        for name, model in targets.items():
            assert model.mesh is not None, f"{name}: mesh is None"
            assert model.spin is not None, f"{name}: spin is None"
            assert model.mesh.vertices.shape[1] == 3, f"{name}: wrong vertex shape"
            assert len(model.mesh.faces) > 100, f"{name}: too few faces ({len(model.mesh.faces)})"
            assert model.spin.period_hours > 0, f"{name}: invalid period"

            # Verify .obj file was saved
            obj_path = os.path.join(tmpdir, f"{name.lower()}.obj")
            assert os.path.exists(obj_path), f"{name}: .obj file not saved"

            print(f"  {name}: {len(model.mesh.vertices)} verts, "
                  f"{len(model.mesh.faces)} faces, "
                  f"P={model.spin.period_hours:.3f}h")

    print("PASS: Synthetic validation targets (>= 3)")


def test_synthetic_lightcurve_generation():
    """Test synthetic lightcurve generation for a validation target."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model = generate_synthetic_validation_target(
            name="TestAsteroid", asteroid_id=999,
            a_axis=2.0, b_axis=1.0, c_axis=0.8,
            pole_lambda=45, pole_beta=30, period_hours=6.0,
            output_dir=tmpdir
        )

        lightcurves = generate_synthetic_lightcurves(model, n_lightcurves=3,
                                                     n_points_per_lc=50)

        assert len(lightcurves) == 3, f"Expected 3 lightcurves, got {len(lightcurves)}"
        for i, lc in enumerate(lightcurves):
            assert len(lc.points) == 50, f"LC {i}: expected 50 points, got {len(lc.points)}"
            mags = lc.mag_array
            assert np.all(np.isfinite(mags)), f"LC {i}: non-finite magnitudes"

        print("PASS: Synthetic lightcurve generation")


def test_dense_lightcurve_properties():
    """Test DenseLightcurve dataclass properties."""
    points = [PhotometryPoint(jd=2451545.0 + i * 0.01, mag=12.0 + 0.1 * i)
              for i in range(10)]
    lc = DenseLightcurve(asteroid_name="Test", points=points)

    assert len(lc.jd_array) == 10
    assert len(lc.mag_array) == 10
    assert abs(lc.jd_array[0] - 2451545.0) < 1e-10
    assert abs(lc.mag_array[5] - 12.5) < 1e-10
    print("PASS: DenseLightcurve properties")


if __name__ == '__main__':
    print("=" * 60)
    print("Data Ingestion Tests")
    print("=" * 60)
    test_parse_alcdef_string()
    test_parse_damit_shape()
    test_parse_damit_spin()
    test_dense_lightcurve_properties()
    test_synthetic_lightcurve_generation()
    test_synthetic_validation_targets()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
