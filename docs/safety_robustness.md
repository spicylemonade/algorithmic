# Safety and Robustness Mechanisms

Detectors and thresholds:
- Policy collapse: trigger if policy entropy < `0.4`.
- Resignation exploit loop: trigger if resignation rate > `0.75`.
- Value-head saturation: trigger if value prediction std < `0.05`.
- Replay mode collapse: trigger if replay uniqueness ratio < `0.60`.

Rollback actions:
- Rewind to last healthy checkpoint window (`~2000` steps).
- Apply optimizer LR backoff (`x0.5`).
- Replace low-diversity replay tail (`30%` refresh).

Simulation evidence:
- See `results/item_015_safety_simulation.json`; all four detectors trigger within 50 steps.
