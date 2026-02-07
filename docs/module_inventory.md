# Module Inventory and Package Boundaries

## Repo Root Inventory Coverage (100%)
Root entries observed in `/home/codex/work/repo`:
1. `.archivara/` - local project metadata directory.
2. `.git/` - git metadata.
3. `TASK_researcher.md` - project brief and execution requirements.
4. `figures/` - generated experiment plots.
5. `main.py` - previous placeholder entry point.
6. `research_rubric.json` - phase/item status tracker.
7. `results/` - structured experiment outputs.
8. `data/` - downloaded and derived datasets.
9. `docs/` - design and protocol documentation.
10. `scripts/` - utility scripts (rubric updater, runners).
11. `src/` - core inversion engine code.

Coverage statement: all root files/directories are accounted for above.

## Proposed LCI Package Map
Target package: `src/lci/`

Planned modules:
1. `lci.config` - deterministic configuration, constants, seed control.
2. `lci.data_contracts` - source schemas and validation.
3. `lci.geometry` - mesh representation, normals, volume, intersection helpers.
4. `lci.photometry` - scattering/brightness forward model.
5. `lci.orbits` - viewing geometry and aspect-angle computations from MPC-like elements.
6. `lci.convex_optimizer` - gradient-based convex inversion core.
7. `lci.sparse_solver` - sparse cadence inversion and restart scheduling.
8. `lci.evolutionary` - non-convex mutation/crossover/selection engine.
9. `lci.hybrid_optimizer` - staged coupling of convex and evolutionary solvers.
10. `lci.metrics` - chi-square, period/pole errors, Hausdorff, volumetric IoU.
11. `lci.priors` - physical plausibility priors (spin/shape/inertia).
12. `lci.uncertainty` - bootstrap/multistart confidence intervals.
13. `lci.pipeline` - orchestration for validation and target modeling.
14. `lci.selection` - candidate filtering and ranking logic.
15. `lci.io` - parsers/writers for ALCDEF/PDS/Gaia/ZTF/DAMIT/JPL and OBJ export.

## Dependency Edges
Explicit dependency graph edges:
- `lci.pipeline -> lci.config`
- `lci.pipeline -> lci.io`
- `lci.pipeline -> lci.hybrid_optimizer`
- `lci.pipeline -> lci.metrics`
- `lci.hybrid_optimizer -> lci.convex_optimizer`
- `lci.hybrid_optimizer -> lci.evolutionary`
- `lci.convex_optimizer -> lci.photometry`
- `lci.convex_optimizer -> lci.geometry`
- `lci.sparse_solver -> lci.convex_optimizer`
- `lci.sparse_solver -> lci.orbits`
- `lci.evolutionary -> lci.geometry`
- `lci.evolutionary -> lci.photometry`
- `lci.metrics -> lci.geometry`
- `lci.uncertainty -> lci.hybrid_optimizer`
- `lci.selection -> lci.data_contracts`
- `lci.io -> lci.data_contracts`
- `lci.priors -> lci.geometry`

Design note: inversion logic resides in `convex_optimizer`, `evolutionary`, `sparse_solver`, and `hybrid_optimizer` implemented from first principles; external libraries are used only for linear algebra and plotting support.
