# Data Contracts for LCI Pipeline Inputs

All timestamps are normalized to `JD_TDB` internally.

## 1) ALCDEF (Dense Light Curves)
Required fields: `object_id`, `obs_code`, `jd_utc`, `mag`, `mag_err`, `filter`, `ra_deg`, `dec_deg`, `solar_phase_deg`.
Units: `mag` in magnitudes, angles in degrees.
Time standard: source UTC, converted to `JD_TDB`.
Validation rules: `mag_err > 0`, `0 <= solar_phase_deg <= 180`, monotonic `jd_utc` within a session.

## 2) NASA PDS/SBN (Calibrated Sparse)
Required fields: `target`, `instrument`, `jd_tdb`, `reduced_mag`, `sigma_mag`, `helio_dist_au`, `geo_dist_au`, `phase_deg`.
Units: AU, degrees, magnitudes.
Time standard: `JD_TDB`.
Validation rules: finite numeric values, `sigma_mag <= 0.2`, positive distances.

## 3) Gaia DR3 Sparse Photometry
Required fields: `source_id`, `number_mp`, `transit_id`, `jd_tcb`, `g_mag`, `g_mag_err`, `phase_angle_deg`, `epoch_index`.
Units: mag, degrees.
Time standard: TCB converted to TDB.
Validation rules: `g_mag_err < 0.1`, unique `(source_id, transit_id)`.

## 4) ZTF / Pan-STARRS Survey Points
Required fields: `survey`, `object_id`, `mjd_utc`, `filter`, `mag`, `mag_err`, `ra_deg`, `dec_deg`, `field_id`.
Units: magnitudes and degrees.
Time standard: MJD UTC converted to JD TDB.
Validation rules: allowed filters set, `mag_err < 0.2`, no duplicated `(survey, field_id, mjd_utc)`.

## 5) MPC Orbital/Geometry Inputs
Required fields: `packed_designation`, `epoch_mjd`, `a_au`, `e`, `i_deg`, `node_deg`, `argperi_deg`, `M_deg`, `H`, `G`.
Units: AU and degrees.
Time standard: epoch in MJD TT/UTC normalized to JD TDB.
Validation rules: `0<=e<1` for asteroid elliptic orbit, `a_au>0`, `0<=i_deg<=180`.

## 6) DAMIT Shape Model Inputs
Required fields: `model_id`, `object_number`, `rotation_period_h`, `pole_lon_deg`, `pole_lat_deg`, `vertices[]`, `faces[]`.
Units: hours and degrees; mesh unit normalized.
Time standard: N/A for mesh itself.
Validation rules: mesh watertight, face indices valid, pole within spherical bounds.

## 7) JPL Radar Shape Inputs
Required fields: `spk_id`, `name`, `rotation_period_h`, `pole_ra_deg`, `pole_dec_deg`, `mesh_vertices[]`, `mesh_faces[]`, `radar_resolution_m`.
Units: hours, degrees, meters.
Time standard: observation epoch metadata converted to JD TDB when used.
Validation rules: positive `radar_resolution_m`, watertight mesh preferred, no NaN vertices.

## Examples (>=3 each)
See `results/item_004_examples.json` for 21 validated example records (3 per source).
