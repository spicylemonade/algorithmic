# Reproducibility and Experiment Tracking (Item 010)

Required metadata schema for every run:
- `run_id`
- `timestamp_utc`
- `seed` (must be 42 unless explicitly justified)
- `git_commit`
- `config_hash` (SHA256 canonical JSON)
- `data_snapshot_hash` (SHA256 canonical JSON)
- `command`

Policy:
- 100% of experiments must include a metadata JSON record under `results/`.
- Reconstructability requirement: config + data snapshot + commit must reproduce run settings exactly.
- Any missing field invalidates the experiment for comparison tables.
