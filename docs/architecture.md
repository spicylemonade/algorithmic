# Baseline LCI Architecture and Interfaces

## Modules (required 8)

| Module | File | Inputs | Outputs | Responsibility |
|---|---|---|---|---|
| Ingestion | `src/lci/ingestion.py` | source files/API payloads | normalized `Observation[]` | parse and validate photometric records |
| Geometry | `src/lci/geometry.py` | shape params, spin state | `Mesh`, phase transforms | mesh generation and rotational geometry |
| Photometry | `src/lci/photometry.py` | `Mesh`, `SpinState`, `Observation` | predicted magnitude, residuals | forward lightcurve model |
| Convex Solver | `src/lci/convex_solver.py` | observations | `InversionResult` | gradient-style convex initialization |
| Evolutionary Solver | `src/lci/evolutionary_solver.py` | base result + observations | refined `InversionResult` | non-convex evolutionary refinement |
| Sparse Solver | `src/lci/sparse_solver.py` | sparse observations | sparse `InversionResult` | sparse-specific inversion path |
| Validation | `src/lci/validation.py` | predicted/truth models | metric dict | Hausdorff/IoU/spin/period evaluation |
| Orchestration | `src/lci/orchestration.py` | target id + observations | final result artifacts | deterministic end-to-end execution |

## Interface Contracts
- `IngestionModule.load_csv(path) -> list[Observation]`
- `GeometryModule.ellipsoid_mesh(a,b,c) -> Mesh`
- `PhotometryModule.predict_magnitude(mesh, spin, obs, jd_ref) -> float`
- `ConvexSolver.solve(asteroid_id, observations) -> InversionResult`
- `EvolutionarySolver.refine(base_result, observations) -> InversionResult`
- `SparseSolver.solve_sparse(asteroid_id, observations) -> InversionResult`
- `ValidationModule.evaluate(pred, truth) -> dict[str,float]`
- `LCIPipeline.solve_dense/solve_sparse(...) -> InversionResult`

## Determinism
- Global stochastic modules use seed `42`.
- Stable ordering for observations and deterministic I/O output serialization.
