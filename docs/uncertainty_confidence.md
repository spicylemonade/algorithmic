# Uncertainty Quantification and Confidence (Item 014)

Approach:
- Bootstrap resampling (`n=200`, seed `42`) of inversion outputs.
- Report percentile intervals (`p05`, `p95`) for period and pole coordinates.
- Derive calibrated confidence score in `[0,1]` from interval width.

Confidence calibration:
- Narrow intervals -> score near 1.
- Wide intervals -> score near 0.
- Score formula clipped to strict `[0,1]` bounds.
