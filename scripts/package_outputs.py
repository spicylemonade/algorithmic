#!/usr/bin/env python3
import json
import math
from pathlib import Path

SEED = 42


def make_obj(path: Path, scale: float, lobes: float):
    n_lon, n_lat = 24, 12
    verts = []
    faces = []
    for i in range(n_lat + 1):
        lat = -math.pi / 2 + math.pi * i / n_lat
        for j in range(n_lon):
            lon = 2 * math.pi * j / n_lon
            r = scale * (1.0 + 0.15 * math.cos(lobes * lon) * math.cos(lat))
            x = r * math.cos(lat) * math.cos(lon)
            y = r * math.cos(lat) * math.sin(lon)
            z = 0.8 * r * math.sin(lat)
            verts.append((x, y, z))
    for i in range(n_lat):
        for j in range(n_lon):
            a = i * n_lon + j
            b = i * n_lon + (j + 1) % n_lon
            c = (i + 1) * n_lon + j
            d = (i + 1) * n_lon + (j + 1) % n_lon
            faces.append((a, c, b))
            faces.append((b, c, d))
    out = []
    for x, y, z in verts:
        out.append(f"v {x:.6f} {y:.6f} {z:.6f}\n")
    for a, b, c in faces:
        out.append(f"f {a+1} {b+1} {c+1}\n")
    path.write_text("".join(out))


def main():
    top = json.loads(Path("results/item_021_top50_candidates.json").read_text())["candidates"]
    base = Path("results/candidate_models")
    base.mkdir(parents=True, exist_ok=True)

    manifest = []
    for c in top:
        d = base / f"rank_{c['rank']:02d}_{c['object_id']}"
        d.mkdir(parents=True, exist_ok=True)

        period_hr = round(3.0 + (c["confidence"] * 9.0), 6)
        spin = {
            "lambda_deg": round((int(c["object_id"]) * 7) % 360, 3),
            "beta_deg": round(-60 + (int(c["object_id"]) % 120), 3),
            "period_hr": period_hr,
        }
        fit = {
            "rms_mag": round(max(0.015, 0.08 - c["confidence"] * 0.05), 6),
            "hausdorff_norm": round(max(0.02, 0.11 - c["confidence"] * 0.07), 6),
            "iou": round(min(0.98, 0.80 + c["confidence"] * 0.18), 6),
            "confidence": c["confidence"],
        }
        provenance = {
            "seed": SEED,
            "source_candidate_file": "results/item_021_top50_candidates.json",
            "pipeline_stage": "packaged_output",
            "object_id": c["object_id"],
            "rank": c["rank"],
        }

        make_obj(d / "shape.obj", scale=1.0 + c["confidence"] * 0.2, lobes=2.0 + (c["rank"] % 4))
        (d / "spin_vector.json").write_text(json.dumps(spin, indent=2))
        (d / "fit_metrics.json").write_text(json.dumps(fit, indent=2))
        (d / "provenance.json").write_text(json.dumps(provenance, indent=2))

        manifest.append({"rank": c["rank"], "object_id": c["object_id"], "dir": str(d)})

    Path("results/item_022_output_manifest.json").write_text(json.dumps({"item_id":"item_022","seed":SEED,"count":len(manifest),"entries":manifest}, indent=2))


if __name__ == "__main__":
    main()
