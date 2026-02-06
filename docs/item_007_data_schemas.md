# External Data Schemas

## ALCDEF (Dense photometry)
Required fields:
- `mpc_designation` (string)
- `jd_utc` (float, days)
- `mag` (float, mag)
- `mag_err` (float, mag)
- `filter` (string)
- `observer_code` (string)
- `reduced_mag_flag` (bool)
Null handling:
- drop row if `jd_utc` or `mag` null
- impute `mag_err` with source median if missing

## NASA PDS Small Bodies Node
Required fields:
- `target_name` (string)
- `time_utc` (ISO8601)
- `flux` (float, calibrated units)
- `flux_err` (float)
- `instrument` (string)
- `calibration_level` (int)
Null handling:
- reject if `calibration_level < 2`
- require uncertainty for weighting; fallback uncertainty = robust MAD

## Gaia DR3 SSO photometry
Required fields:
- `source_id` (int64)
- `epoch` (BJD/TCB float days)
- `g_mag` (float, mag)
- `g_mag_error` (float, mag)
- `phase_angle_deg` (float)
- `heliocentric_distance_au` (float)
- `observer_distance_au` (float)
Null handling:
- remove rows missing `epoch` or `g_mag`
- cap `g_mag_error` at 0.1 mag for robust weighting floor

## ZTF / Pan-STARRS sparse surveys
Required fields:
- `object_id` (string)
- `mjd` (float, days)
- `mag_psf` (float, mag)
- `sigmag_psf` (float)
- `filter_id` (string)
- `field_id` (string/int)
- `quality_flag` (int)
Null handling:
- discard rows with failing quality flags
- normalize filter zero-points via per-survey bias term

## MPC (Orbital geometry)
Required fields:
- `packed_designation` (string)
- `epoch_mjd` (float)
- `a_au`, `e`, `i_deg`, `node_deg`, `argperi_deg`, `mean_anomaly_deg` (floats)
Null handling:
- no null tolerance for orbital elements; record excluded targets

## DAMIT (Validation shape models)
Required fields:
- `asteroid_id` (string/int)
- `model_file` (`.obj`/`.mod`)
- `pole_lambda_deg`, `pole_beta_deg`, `period_h` (floats)
- `quality_note` (string)
Null handling:
- if pole/period absent, model can be used for geometry-only comparisons

## JPL Radar shape models
Required fields:
- `target` (string)
- `mesh_file` (string)
- `resolution_m` (float)
- `spin_axis` (vector)
- `reference_frame` (string)
Null handling:
- keep mesh-only entries, mark spin fields as optional

## Canonical Normalized Record (internal)
- `target_id` string
- `time_jd` float (days)
- `flux` float (relative)
- `flux_err` float
- `sun_vec` (x,y,z)
- `obs_vec` (x,y,z)
- `phase_angle_deg` float
- `apparition_id` int
- `source` enum (`ALCDEF|PDS|GAIA|ZTF|PANSTARRS`)
