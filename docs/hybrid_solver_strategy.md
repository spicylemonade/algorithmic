# Hybrid Convex + Evolutionary Strategy (Item 011)

Staged optimization:
1. Run convex inversion to convergence for deterministic global scaffold.
2. Convert convex parameterization to non-convex gene vector.
3. Run GA refinement using seeded population around convex result.
4. Select best non-convex candidate under multi-objective loss.

Operators:
- Crossover: single-point recombination of shape gene vectors.
- Mutation: bounded random perturbation per gene.
- Elitism: top `4` candidates preserved each generation.

Termination criteria:
- Max generations: `120`.
- Stall stop: no improvement for `20` generations.
- Optional target-loss threshold (configured externally).
