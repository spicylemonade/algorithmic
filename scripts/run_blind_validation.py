#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lci.geometry import GeometryModule
from lci.orchestration import LCIPipeline
from lci.types import InversionResult, Observation, SpinState
from lci.validation import ValidationModule


def write_obj(path: Path, vertices: list[list[float]], faces: list[list[int]]) -> None:
    with path.open("w") as f:
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        for tri in faces:
            f.write(f"f {tri[0]+1} {tri[1]+1} {tri[2]+1}\n")


def synth_observations(spin: SpinState, n=220, seed=42):
    rng = random.Random(seed)
    obs = []
    jd0 = 2460100.0
    for i in range(n):
        jd = jd0 + i * 0.05
        phase = 8.0 + 40.0 * abs(math.sin(i / 50.0))
        rot = 2.0 * math.pi * (jd - jd0) / (spin.period_hours / 24.0)
        mag = 15.2 + 0.018 * phase - 0.33 * math.sin(rot + math.radians(spin.phi0_deg))
        mag += rng.uniform(-0.03, 0.03)
        obs.append(Observation(jd=jd, mag=mag, sigma=0.03, phase_angle_deg=phase, source="blind_synth"))
    return obs


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "results/item_010_benchmark_manifest.json").read_text())
    out_dir = root / "results/blind_validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    model_dir = out_dir / "models"
    model_dir.mkdir(exist_ok=True)

    geom = GeometryModule()
    valid = ValidationModule()
    pipe = LCIPipeline(seed=42)

    summaries = []
    for idx, t in enumerate(manifest["targets"]):
        number = t["number"]
        asteroid_id = str(number)

        truth_spin = SpinState(
            lambda_deg=(90 + 17 * idx) % 360,
            beta_deg=max(-70.0, min(70.0, -25 + 9 * idx)),
            period_hours=4.8 + 0.37 * (idx % 8),
            phi0_deg=15.0 + idx,
        )
        truth_mesh = geom.ellipsoid_mesh(1.0 + 0.03 * (idx % 3), 0.85 + 0.02 * (idx % 4), 0.72 + 0.01 * (idx % 5))
        truth = InversionResult(asteroid_id=asteroid_id, mesh=truth_mesh, spin=truth_spin, metrics={})

        observations = synth_observations(truth_spin, n=220, seed=42 + idx)

        # Blind solve: truth is not passed into solver.
        pred = pipe.solve_dense(asteroid_id, observations)

        metrics = valid.evaluate(pred, truth)
        pred.metrics.update(metrics)

        pred_obj = model_dir / f"{asteroid_id}_pred.obj"
        truth_obj = model_dir / f"{asteroid_id}_truth.obj"
        write_obj(pred_obj, pred.mesh.vertices, pred.mesh.faces)
        write_obj(truth_obj, truth.mesh.vertices, truth.mesh.faces)

        rec = {
            "asteroid_id": asteroid_id,
            "name": t["name"],
            "predicted_obj": str(pred_obj.relative_to(root)),
            "truth_obj": str(truth_obj.relative_to(root)),
            "metrics": metrics,
            "predicted_spin": pred.spin.__dict__,
            "truth_spin": truth_spin.__dict__,
            "n_observations": len(observations),
        }
        (out_dir / f"{asteroid_id}_prediction.json").write_text(json.dumps(rec, indent=2) + "\n")
        summaries.append(rec)

    payload = {
        "item_id": "item_016",
        "seed": 42,
        "blind_protocol": "truth excluded from optimization; used only for post-fit metrics",
        "targets": summaries,
    }
    (root / "results/item_016_blind_validation.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
