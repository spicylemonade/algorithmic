# Blind Validation Protocol

- Use benchmark target list from `results/item_010_benchmark_manifest.json`.
- Generate calibrated synthetic raw lightcurves per target; hide truth mesh/spin during solving.
- Run dense pipeline (`LCIPipeline.solve_dense`) for each target.
- After optimization, compute metrics against held-out truth meshes/spins.
- Store per-target prediction JSON, predicted/truth OBJ mesh artifacts, and aggregated log.

Execution:
`python scripts/run_blind_validation.py`

Outputs:
- `results/item_016_blind_validation.json`
- `results/blind_validation/*_prediction.json`
- `results/blind_validation/models/*.obj`
