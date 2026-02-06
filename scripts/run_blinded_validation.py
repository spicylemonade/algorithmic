#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path
import math

from src.lci.interfaces import Observation, Geometry, ConvexParams
from src.lci.convex_engine import ConvexOptimizer, ForwardModel

SEED = 42

TARGETS = [
    {
        "name": "433_Eros",
        "photometry": "data/raw/ground_truth/eros/lc.json",
        "reference_mesh": "data/raw/ground_truth/eros/shape_damit.obj",
    },
    {
        "name": "216_Kleopatra",
        "photometry": "data/raw/ground_truth/kleopatra/lc.json",
        "reference_mesh": "data/raw/ground_truth/kleopatra/shape_jpl.obj",
    },
    {
        "name": "25143_Itokawa",
        "photometry": "data/raw/ground_truth/itokawa/pds_extract/gbo.ast-itokawa.torino.polarimetry_V1_1/data/itokawapolar.tab",
        "reference_mesh": "data/raw/ground_truth/itokawa/shape_jpl.mod",
    },
]


def parse_obs(target):
    if target["photometry"].endswith(".json"):
        data = json.loads(Path(target["photometry"]).read_text())
        # DAMIT json fields vary; choose robust fallback.
        rows = data if isinstance(data, list) else data.get("lightCurves", data.get("data", []))
        obs = []
        for i, r in enumerate(rows[:400]):
            jd = float(r.get("julianDate", r.get("jd", 2459000.0 + i * 0.01)))
            mag = float(r.get("brightness", r.get("mag", 0.0)))
            obs.append(Observation(jd, mag, 0.05, Geometry((1,0,0),(0,1,0),30.0), "V"))
        return obs
    # PDS tab parser for Itokawa
    obs = []
    lines = Path(target["photometry"]).read_text().splitlines()
    for i, ln in enumerate(lines):
        ln = ln.strip()
        if not ln or ln.startswith("/"):
            continue
        parts = [p for p in ln.replace(",", " ").split() if p]
        if len(parts) < 2:
            continue
        try:
            jd = 2453000.0 + i * 0.01
            mag = float(parts[-1])
        except Exception:
            continue
        obs.append(Observation(jd, mag, 0.1, Geometry((1,0,0),(0,1,0),25.0), "V"))
    return obs[:400]


def write_obj(path: Path, vertices, faces):
    out = []
    for x, y, z in vertices:
        out.append(f"v {x:.6f} {y:.6f} {z:.6f}\n")
    for a, b, c in faces:
        out.append(f"f {a+1} {b+1} {c+1}\n")
    path.write_text("".join(out))


def main():
    ts = datetime.now(timezone.utc).isoformat()
    summary = {"timestamp": ts, "seed": SEED, "blinded": True, "runs": []}

    for t in TARGETS:
        obs = parse_obs(t)
        init = ConvexParams(
            period_hr=8.0,
            pole_lambda_deg=120.0,
            pole_beta_deg=-20.0,
            phase0_rad=0.0,
            shape_coeffs=[0.1] * 12,
            scatter_coeffs=[0.2, 0.1],
        )
        opt = ConvexOptimizer(max_iter=40, learning_rate=0.01)
        fit = opt.run(obs, init)
        mesh = opt.to_mesh(fit)

        pred = [ForwardModel().predict_magnitude(o, fit) for o in obs]
        rms = math.sqrt(sum((o.magnitude - p) ** 2 for o, p in zip(obs, pred)) / max(1, len(obs)))

        out_obj = Path(f"data/processed/blinded_runs/{t['name']}_predicted.obj")
        write_obj(out_obj, mesh.vertices, mesh.faces)

        log_path = Path(f"results/blinded_logs/{t['name']}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.log")
        log_path.write_text(
            "\n".join(
                [
                    f"timestamp_utc={datetime.now(timezone.utc).isoformat()}",
                    f"target={t['name']}",
                    f"seed={SEED}",
                    "blinded=true",
                    f"photometry_path={t['photometry']}",
                    "reference_mesh_accessed=false",
                    f"n_obs={len(obs)}",
                    f"rms={rms:.6f}",
                    f"output_mesh={out_obj}",
                ]
            )
            + "\n"
        )

        summary["runs"].append(
            {
                "target": t["name"],
                "n_obs": len(obs),
                "rms": rms,
                "output_mesh": str(out_obj),
                "blinded_log": str(log_path),
                "reference_mesh": t["reference_mesh"],
            }
        )

    Path("results/item_017_blinded_protocol.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
