#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

from lci.config import set_global_seed
from lci.convex_optimizer import model_mags
from lci.geometry import ellipsoid_points
from lci.metrics import structured_report


set_global_seed(42)
rng = np.random.default_rng(42)
true_params = np.array([1.2, 0.9, 0.7, 6.5, 1.2, 0.3])
est_params = np.array([1.18, 0.92, 0.71, 6.54, 1.25, 0.28])
t = np.linspace(0, 10, 120)
s = np.array([1.0, 0.1, 0.2])
o = np.array([0.4, -0.5, 0.7])

obs = model_mags(true_params, t, s, o) + rng.normal(0, 0.01, size=t.size)
pred = model_mags(est_params, t, s, o)
true_pts = ellipsoid_points(*true_params[:3], n=600)
est_pts = ellipsoid_points(*est_params[:3], n=600)

report = structured_report(
    obs_mag=obs,
    pred_mag=pred,
    true_period=float(true_params[3]),
    est_period=float(est_params[3]),
    true_pole=(float(true_params[4]), float(true_params[5])),
    est_pole=(float(est_params[4]), float(est_params[5])),
    true_points=true_pts,
    est_points=est_pts,
)
out = {
    "item_id": "item_009",
    "seed": 42,
    "metrics": report,
    "required_fields_present": all(
        k in report
        for k in ["chi_square", "period_error_pct", "pole_error_deg", "hausdorff_distance", "volumetric_iou"]
    ),
}
Path("results/item_009_metrics_report.json").write_text(json.dumps(out, indent=2) + "\n")
