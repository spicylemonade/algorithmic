# Repository Inventory

| Path | Type | Purpose | Dependency Notes |
|---|---|---|---|
| `.archivara` | directory | Agent execution logs and orchestration metadata | Read-only for diagnostics; no runtime dependency |
| `.git` | directory | Git repository metadata | Required for commit/version tracking only |
| `TASK_researcher.md` | file | Research task instructions for this agent | Guides execution order and deliverables |
| `data` | directory | Downloaded and intermediate datasets | Feeds inversion and validation pipeline |
| `docs` | directory | Design and analysis documentation | Generated from analysis scripts/results artifacts |
| `figures` | directory | Output PNG visualizations for experiments | Populated by plotting scripts from results/* |
| `main.py` | file | Project entrypoint placeholder | Will call src/lci pipeline modules |
| `models` | directory | Ground truth and generated 3D meshes | Feeds mesh comparison metrics (Hausdorff/IoU) |
| `research_rubric.json` | file | Execution rubric and progress tracker | Updated by tools/update_rubric.py before/after each item |
| `results` | directory | Structured experiment outputs in JSON | Consumed by reports and ranking outputs |
| `src` | directory | LCI package source code | Depends on standard Python runtime + optional C++ acceleration |
| `tools` | directory | Research utility scripts (rubric updates, data tooling) | Depends on Python stdlib and occasional third-party libs |

## Missing Expected Assets
- `TASK_orchestrator.md` is referenced by acceptance criteria but not present in this repository.
