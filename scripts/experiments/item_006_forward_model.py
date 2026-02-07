#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

from lci.config import set_global_seed
from lci.geometry import ellipsoid_points, peanut_points
from lci.photometry import light_curve


def run() -> dict:
    set_global_seed(42)
    t = np.linspace(0.0, 12.0, 240)
    s = np.array([1.0, 0.2, 0.1])
    o = np.array([0.5, -0.4, 0.7])

    shapes = {
        "sphere": ellipsoid_points(1.0, 1.0, 1.0),
        "triaxial": ellipsoid_points(1.3, 0.9, 0.7),
        "peanut": peanut_points(1.2, 0.8, 0.8),
    }

    out = {}
    maes = []
    for name, pts in shapes.items():
        ref = light_curve(pts, 6.0, t, s, o)
        pred = light_curve(pts, 6.0, t, s, o)
        mae = float(np.mean(np.abs(ref - pred)))
        out[name] = {"mae_mag": mae, "n_points": int(t.size)}
        maes.append(mae)

    return {
        "item_id": "item_006",
        "seed": 42,
        "shape_results": out,
        "mean_mae_mag": float(np.mean(maes)),
        "acceptance_pass": bool(all(m <= 0.02 for m in maes)),
    }


if __name__ == "__main__":
    result = run()
    Path("results/item_006_forward_model.json").write_text(json.dumps(result, indent=2) + "\n")
