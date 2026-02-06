# Ablation and Stress-Test Campaign (Item 019)

Ablations executed (8 total):
1. Sparse density increase (200 pts)
2. Sparse density reduction (80 pts)
3. Wide phase-angle coverage
4. Narrow phase-angle coverage
5. Low noise (`sigma=0.02`)
6. High noise (`sigma=0.08`)
7. Disable evolutionary non-convex module
8. Disable sparse-prior regularization

Reported deltas include:
- Hausdorff distance
- Volumetric IoU
- Photometric RMS
- Pole angular error

See `results/item_019_ablations.json` for full metric deltas per ablation.
