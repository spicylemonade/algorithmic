# Reproducible Data Ingestion Schema

## Canonical Observation Schema
| Field | Type | Unit | Required | Description |
|---|---|---|---|---|
| `object_id` | string | n/a | yes | MPC packed or numbered designation |
| `jd` | float | day (TDB/UTC tagged) | yes | observation timestamp |
| `mag` | float | mag | yes | reduced/observed magnitude |
| `sigma_mag` | float | mag | yes | photometric uncertainty |
| `filter` | string | n/a | yes | bandpass code |
| `phase_angle_deg` | float | degree | yes | Sun-target-observer angle |
| `r_au` | float | AU | yes | heliocentric distance |
| `delta_au` | float | AU | yes | observer distance |
| `observer_code` | string | n/a | yes | observatory/survey code |
| `source_name` | enum | n/a | yes | one of ALCDEF/PDS/GAIA_DR3/ZTF/PANSTARRS |
| `source_record_id` | string | n/a | yes | source-native identifier |
| `provenance_hash` | string | n/a | yes | SHA256 over source row payload |

## Source Parse Rules

### ALCDEF
- Parse session blocks and observation rows into canonical fields.
- Time normalization to JD UTC.
- Validate mandatory fields: station, filter, magnitude, uncertainty.

### NASA PDS SBN
- Parse calibrated photometry tables (`.tab/.lbl` or bundled CSV).
- Validate label/table consistency and units from metadata labels.

### Gaia DR3
- Parse epoch photometry rows, convert flux to magnitude where needed.
- Keep Gaia source id and processing flags for quality filtering.

### ZTF
- Parse alert/history CSV with photometric quality flags.
- Enforce quality constraints (`catflags=0`, finite errors).

### Pan-STARRS
- Parse object detection records and calibration metadata.
- Use only calibrated magnitudes with survey quality bitmask pass.

### MPC
- Parse orbital elements/ephemeris needed for geometry interpolation.
- Validate epoch and element covariance availability.

## Validation Checks
- Physical range checks:
  - `0 <= phase_angle_deg <= 180`
  - `sigma_mag > 0`
  - `r_au > 0`, `delta_au > 0`
- Time monotonicity optional per apparition grouping.
- Duplicate suppression by `(source_name, source_record_id)`.
- Provenance required for every output row.

## Provenance Tags
Each row stores:
- `source_name`
- `source_url`
- `downloaded_at_utc`
- `license_note`
- `parser_version`
