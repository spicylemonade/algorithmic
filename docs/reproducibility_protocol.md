# Deterministic Experiment Protocol

## Determinism Standard
- Global seed: `42` for `random` and `numpy`.
- Any stochastic operator receives explicit per-run seed derived as `seed = 42 + run_index`.
- Input ordering must be sorted by object id and timestamp before optimization.

## Hardware Profile Template
- CPU model + core count
- RAM size
- OS + kernel
- Python version
- BLAS backend details

## Environment and Version Pinning
- Python dependencies pinned in `requirements.txt` (or lockfile).
- Store `git commit SHA`, uncommitted diff hash, and config snapshot per run.
- Save all run configs in `results/run_manifests/*.json`.

## Run Procedure
1. Initialize workspace and seed (`42`).
2. Validate schemas for all input streams.
3. Execute phase-specific pipelines in fixed order.
4. Write intermediate outputs to `results/` and plots to `figures/`.
5. Compute pass/fail gate for each phase.
6. Archive run manifest with checksums.

## Pass/Fail Gates by Project Phase
- Phase 1 gate: architecture docs complete and data contracts validated.
- Phase 2 gate: convex and sparse baselines meet synthetic recovery thresholds.
- Phase 3 gate: hybrid/adaptive/prior/UQ modules show objective and uncertainty improvements.
- Phase 4 gate: benchmark runs complete for all selected objects; recursive retuning triggered if normalized mesh deviation >5%.
- Phase 5 gate: deterministic top-50 candidate list and artifact bundle produced with provenance.

## Failure Policy
- Mark rubric item as `failed` with explicit error.
- Continue to next item without halting whole experiment.
- Preserve failed run artifacts for auditability.
