# Blinded Reconstruction Protocol (Item 017)

Protocol guarantees:
- Inversion stage loads only raw photometry files.
- Reference meshes are excluded from solver inputs.
- Per-target timestamped logs written under `results/blinded_logs/` with `reference_mesh_accessed=false`.

Execution command:
- `PYTHONPATH=. ./scripts/run_blinded_validation.py`

Outputs:
- Predicted meshes: `data/processed/blinded_runs/*_predicted.obj`
- Blinded logs: `results/blinded_logs/*.log`
- Summary manifest: `results/item_017_blinded_protocol.json`
