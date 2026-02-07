#!/usr/bin/env python3
import json
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lci.convex_solver import ConvexSolver
from lci.types import Observation


def synth_obs(n=180, seed=42):
    rng = random.Random(seed)
    obs = []
    jd0 = 2460000.0
    for i in range(n):
        jd = jd0 + 0.08 * i
        phase = 5 + 45 * (i / n)
        mag = 14.8 + 0.2 * (1 + rng.uniform(-0.2, 0.2)) * __import__("math").sin(i / 13.0)
        mag += 0.02 * phase + rng.uniform(-0.03, 0.03)
        obs.append(Observation(jd=jd, mag=mag, sigma=0.03, phase_angle_deg=phase, source="synthetic"))
    return obs


def run():
    observations = synth_obs(seed=42)
    configs = [
        {"id": "A", "step_size": 0.05, "max_iter": 300},
        {"id": "B", "step_size": 0.04, "max_iter": 320},
        {"id": "C", "step_size": 0.06, "max_iter": 280},
    ]

    rows = []
    for c in configs:
        solver = ConvexSolver(step_size=c["step_size"], max_iter=c["max_iter"])
        out = solver.solve("synthetic_asteroid", observations)
        rows.append(
            {
                "run_id": c["id"],
                "seed": 42,
                "step_size": c["step_size"],
                "max_iter": c["max_iter"],
                "photometric_rms": out.metrics["photometric_rms"],
                "lambda_deg": out.spin.lambda_deg,
                "beta_deg": out.spin.beta_deg,
                "period_hours": out.spin.period_hours,
            }
        )

    payload = {
        "item_id": "item_008",
        "protocol": "docs/convex_baseline_protocol.md",
        "runs": rows,
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/item_008_baseline_protocol.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    run()
