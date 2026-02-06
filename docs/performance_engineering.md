# Performance Engineering Plan (Item 015)

Top planned bottlenecks:
1. Forward-model flux accumulation across facets and epochs.
2. Finite-difference gradient evaluation across shape coefficients.
3. Genetic population scoring during non-convex refinement.

Python/C++ boundary:
- Keep orchestration, IO, and adaptive control in Python.
- Move heavy kernels to C++ extension:
  - facet visibility + brightness accumulation,
  - Jacobian/gradient block operations,
  - batch candidate objective evaluation.

Target speedups:
- Kernel 1 (forward model): `>=6x`
- Kernel 2 (gradient block): `>=8x`
- Kernel 3 (GA scoring): `>=5x`

Numerical consistency checks:
- Compare C++ vs Python outputs on fixed seed (`42`) and fixed data snapshots.
- Required max absolute difference:
  - magnitudes: `<1e-8`
  - loss values: `<1e-9`
  - gradient components: `<1e-6`
