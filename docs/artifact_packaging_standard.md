# Final Artifact Packaging Standard

For every modeled target, package must include:
1. `shape.obj` - final reconstructed mesh.
2. `spin_vector.json` - pole longitude/latitude, period, phase reference.
3. `run_config.json` - solver settings, weights, seed (`42`), data sources.
4. `metrics_summary.json` - fit residuals + validation metrics.
5. `provenance_manifest.json` - source URLs, download timestamps, parser versions, checksums.

Directory layout:
`results/final_models/<asteroid_number>/`
- `shape.obj`
- `spin_vector.json`
- `run_config.json`
- `metrics_summary.json`
- `provenance_manifest.json`
