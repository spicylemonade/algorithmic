# Repository Inventory

| Path | Type | Purpose | Dependencies / Links |
|---|---|---|---|
| `.archivara/` | directory | Agent runtime logs and session metadata | Feeds process traceability for rubric execution |
| `.git/` | directory | Version control metadata | Required for per-item commit trail |
| `docs/` | directory | Research design, protocol, and reporting artifacts | Referenced by `main.py` and rubric notes |
| `figures/` | directory | Generated PNG plots for experiments | Populated by evaluation scripts |
| `results/` | directory | JSON outputs for experiments and manifests | Populated by pipeline and analysis scripts |
| `scripts/` | directory | Utility executables for rubric updates and experiments | Called from shell and `main.py` orchestration |
| `main.py` | file | Entry-point for running the inversion pipeline workflows | Imports `src/` modules and writes `results/` + `figures/` |
| `research_rubric.json` | file | Canonical progress tracker for all 25 research items | Updated before/after each item via `scripts/update_rubric.py` |
| `TASK_researcher.md` | file | Research assignment and execution constraints | Drives item-by-item implementation behavior |
| `TASK_orchestrator.md` | file | Orchestrator handoff/task trace file | Linked to top-level multi-agent workflow |

## Root dependency graph (high level)

- `main.py` depends on source modules in `src/` (to be implemented) and writes outputs to `results/` and `figures/`.
- `research_rubric.json` is mutated by `scripts/update_rubric.py` before/after each rubric item.
- `docs/` captures design/validation artifacts consumed by phase-level reporting.
