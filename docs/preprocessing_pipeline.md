# Photometry Preprocessing Pipeline (Item 008)

Deterministic pipeline steps:
1. Parse to canonical schema and sort by `jd`.
2. Calibration normalization: `mag_norm = mag - zeropoint_ref`.
3. Reject points with `mag_err > 0.2` mag.
4. Sigma-clipped outlier rejection with threshold `3.5 sigma`.
5. Apparition segmentation with temporal gap `120 days`.
6. Geometry computation (phase/aspect/elongation) via MPC-derived ephemeris.
7. Drop apparitions with `<12` points for inversion stages requiring dense constraints.

All stochastic modules consume seed `42`; preprocessing itself is deterministic.
