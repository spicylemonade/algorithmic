# Repository Module Map (Item 001)

## Scope Audited
- `TASK_orchestrator.md` (required by rubric; file is currently missing in workspace)
- `TASK_researcher.md`
- `main.py`
- `figures/`
- `results/`
- `.archivara/logs/`
- `research_rubric.json`

## Module Responsibilities
- `research_rubric.json`: canonical execution state machine and acceptance tracking.
- `TASK_researcher.md`: human-readable objective and execution constraints.
- `TASK_orchestrator.md`: expected orchestration spec (missing; treated as external dependency).
- `main.py`: entrypoint placeholder to be replaced by pipeline CLI.
- `.archivara/logs/orchestrator.log`: upstream audit of orchestration decisions.
- `.archivara/logs/researcher.log`: runtime trace of researcher actions.
- `results/`: structured experiment outputs (JSON and generated artifacts).
- `figures/`: rendered visual diagnostics (PNG).

## Upstream/Downstream Dependencies
1. `TASK_orchestrator.md` -> `research_rubric.json`
2. `TASK_researcher.md` -> `research_rubric.json`
3. `research_rubric.json` -> `main.py` (phase-driven execution order)
4. `main.py` -> `results/` and `figures/`
5. `main.py` -> `.archivara/logs/researcher.log`
6. `.archivara/logs/orchestrator.log` -> interpretation context for `research_rubric.json`
7. `results/` -> downstream validation/reporting consumers
8. `figures/` -> downstream validation/reporting consumers

## Gaps
- `TASK_orchestrator.md` not present; dependency retained in map and flagged for fallback handling.
