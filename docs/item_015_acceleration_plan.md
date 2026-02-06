# Performance Acceleration Plan

## Identified Hotspots
1. Facet-wise brightness accumulation (`mesh_brightness`)
2. Sparse period/pole grid search (`solve_sparse`)
3. Hybrid iterative loop (convex finite differences + GA population scoring)

## Optimization Paths
1. Vectorization
- Replace Python loops in brightness and residual calculations with contiguous array kernels.
- Expected speedup target: `3x-6x` on CPU.

2. C++ extension points
- Move repeated facet projection + loss gradient blocks into C++ (`pybind11`) while keeping Python orchestration.
- Expected speedup target: `8x-20x` for gradient-heavy convex stage.

3. Parallel batch evaluation
- Evaluate GA population and period-grid candidate batches concurrently (`multiprocessing`/OpenMP backend).
- Expected speedup target: near-linear up to memory limits (`4x-12x` on 8-16 cores).

4. Caching and memoization
- Cache geometry transforms by phase bin and avoid repeated trigonometric recomputation.
- Expected speedup target: `1.5x-2.5x`.

## Practical Sequence
1. Vectorize + cache (lowest risk)
2. Parallelize population/grid scoring
3. Introduce C++ kernel for brightness/gradient core
