# Benchmark Metric Protocol (Item 009)

Implemented exact algorithms:
- Hausdorff distance: bidirectional nearest-neighbor maximum over mesh samples.
- Volumetric IoU: `|A ∩ B| / |A ∪ B|` over voxelized occupancy sets.
- Lightcurve RMS residual: `sqrt(mean((m_obs - m_pred)^2))`.
- Spin-vector angular error: `acos((v·u)/(|v||u|))` in degrees.

Test fixtures and expected outputs:
- Hausdorff fixture => `1.0`
- IoU fixture => `0.3333333333`
- RMS fixture => `0.5773502692`
- Spin angular fixture => `90.0 deg`
