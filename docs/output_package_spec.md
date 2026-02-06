# Output Package Specification (Item 022)

Directory convention under `results/`:
- `results/candidate_models/rank_<NN>_<OBJECT_ID>/`

Required artifacts per target:
- `shape.obj` (triangulated 3D mesh)
- `spin_vector.json` (lambda, beta, period)
- `fit_metrics.json` (residual and geometric metrics)
- `provenance.json` (seed, source inputs, pipeline stage)

Batch manifest:
- `results/item_022_output_manifest.json`
