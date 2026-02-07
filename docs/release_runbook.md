# Reproducible Release Runbook

## Environment
- Python 3.10+
- Install dependencies: `python3 -m pip install -r requirements.txt`
- Deterministic seed: `42`

## End-to-End Steps
1. Validate repository state and rubric: `cat research_rubric.json`.
2. Run all experiment scripts in `scripts/experiments/` sequentially by item number.
3. Confirm outputs:
   - JSON artifacts in `results/`
   - PNG figures in `figures/`
   - Model exports in `results/models/`
4. Recompute checksums: `python3 scripts/build_checksums.py`.
5. Compare generated checksums with `results/checksums.sha256`.

## Core Manifests
- Rubric/progress: `research_rubric.json`
- Candidate tables: `results/item_021_candidates.json`, `results/item_022_top50.json`
- Final model manifest: `results/item_023_manifest.json`
- Validation report: `docs/validation_report.md`

## Determinism Notes
- Random seeds are fixed in all scripts (`42` or deterministic offsets).
- Selection/ranking and artifact generation are deterministic given unchanged inputs.

## Third-Party Verification Checklist
- [ ] Dependency versions match `requirements.txt`
- [ ] Rubric summary counts match expected terminal state
- [ ] Checksum file validates all tracked outputs
- [ ] Top-50 manifest includes 50 objects with linked mesh/spin artifacts
