# Baseline Convex Engine Architecture (Item 006)

## Interfaces
- `ForwardModel.predict_magnitude(obs, params) -> float`
- `GradientEvaluator.finite_difference(observations, params) -> List[float]`
- `ConvexOptimizer.run(observations, init_params) -> ConvexParams`
- `ConvexOptimizer.to_mesh(params, n_lon, n_lat) -> Mesh`

## Data Flow
1. Ingest canonical observations.
2. Initialize convex parameters.
3. Evaluate forward model magnitudes.
4. Compute finite-difference gradient.
5. Update shape coefficients with gradient descent.
6. Stop on tolerance or max iterations.
7. Convert optimized parameters to triangulated mesh.

## Diagram
`Observation[] -> ForwardModel -> Residuals -> GradientEvaluator -> ConvexOptimizer -> ConvexParams -> Mesh`
