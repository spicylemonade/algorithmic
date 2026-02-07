#!/usr/bin/env python3
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lci.config import set_global_seed
from lci.geometry import ellipsoid_points, peanut_points
from lci.photometry import light_curve

set_global_seed(42)
t = np.linspace(0.0, 12.0, 240)
s = np.array([1.0, 0.2, 0.1])
o = np.array([0.5, -0.4, 0.7])
shapes = {
    "sphere": ellipsoid_points(1.0, 1.0, 1.0),
    "triaxial": ellipsoid_points(1.3, 0.9, 0.7),
    "peanut": peanut_points(1.2, 0.8, 0.8),
}

plt.figure(figsize=(9, 5))
for name, pts in shapes.items():
    mags = light_curve(pts, 6.0, t, s, o)
    plt.plot(t, mags, label=name)
plt.gca().invert_yaxis()
plt.xlabel("Time (h)")
plt.ylabel("Magnitude")
plt.title("Item 006: Synthetic Forward Model Light Curves")
plt.legend()
plt.tight_layout()
Path("figures").mkdir(exist_ok=True)
plt.savefig("figures/item_006_lightcurves.png", dpi=150)

Path("results/item_006_plot_meta.json").write_text(json.dumps({"item_id":"item_006","figure":"figures/item_006_lightcurves.png","seed":42}, indent=2)+"\n")
