# Data Source Contracts and Canonical Schema (Item 004)

## Canonical Observation Schema
- `object_id` (string): MPC packed or number.
- `utc_jd` (float, day): UTC Julian date.
- `tdb_jd` (float, day): TDB Julian date (derived if needed).
- `mag` (float, mag): reduced or calibrated magnitude.
- `mag_sigma` (float, mag): uncertainty.
- `filter_band` (string): photometric band (e.g., V, G, r).
- `observer_code` (string): station or survey identifier.
- `ra_deg`, `dec_deg` (float, deg): sky position.
- `r_helio_au`, `delta_geo_au` (float, AU): geometry distances.
- `phase_angle_deg`, `solar_elongation_deg` (float, deg).
- `ecl_lon_sun_deg`, `ecl_lat_sun_deg` (float, deg).
- `ecl_lon_obs_deg`, `ecl_lat_obs_deg` (float, deg).
- `apparition_id` (string): deterministic segmentation key.
- `source` (enum): alcdef/pds/gaia/ztf/panstarrs/mpc.

## Source Contracts
1. ALCDEF
- Parser: key-value header + tabular block parser.
- Required fields: object, JD, mag, filter, station.
- Unit transforms: JD UTC->TDB; magnitudes preserved.

2. NASA PDS Small Bodies Node
- Parser: PDS4 XML label + table reader.
- Required fields: time, calibrated flux/mag, uncertainty, geometry.
- Unit transforms: flux->mag if needed, radians->deg.

3. Gaia DR3
- Parser: ADQL/CSV ingestion.
- Required fields: `source_id`, epoch, `phot_g_mean_flux`, error.
- Unit transforms: Gaia G flux->mag; BJD->JD conversion metadata.

4. ZTF
- Parser: IPAC CSV/lightcurve API parser.
- Required fields: `mjd`, `mag`, `magerr`, filter, field/ccd.
- Unit transforms: MJD->JD; quality-flag filtering.

5. Pan-STARRS
- Parser: MAST table parser.
- Required fields: detection epoch, mag, err, filter, quality bits.
- Unit transforms: time normalization to JD/TDB.

6. MPC
- Parser: MPCORB + observation format parser.
- Required fields: orbit elements, observation epochs.
- Unit transforms: element epochs to TDB for geometry propagation.

7. DAMIT (validation)
- Parser: `.obj`/`.mod` mesh parser.
- Required fields: vertices, faces, pole, period.
- Unit transforms: mesh normalization to unit volume for comparison.

8. JPL Radar Shapes (validation)
- Parser: OBJ/PLY/shape text parser.
- Required fields: triangulated mesh, spin metadata when available.
- Unit transforms: coordinate frame normalization to body principal axes.

## Harmonization Rules
- All times stored as both UTC JD and TDB JD.
- Magnitudes represented in mag with explicit `filter_band`.
- Geometry columns populated from MPC/JPL ephemeris if absent in source.
- Per-source calibration offsets tracked in provenance metadata.
