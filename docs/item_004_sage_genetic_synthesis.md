# SAGE-Style Non-Convex Evolutionary Modeling

## Chromosome Encoding
Each individual encodes:
- `shape_nodes`: radial offsets of control points on a spherical mesh (`N=256`, bounded in `[0.4, 1.8]` normalized units).
- `spin`: `(lambda, beta, P, phi0)`.
- `scattering`: phase-law coefficients `(A0, k, g)`.

Genome vector:
`c = [r_1, ..., r_N, lambda, beta, P, phi0, A0, k, g]`.

## Fitness Function
`F(c) = - (w_lc * RMSE_lc + w_reg * R_surface + w_phys * R_phys + w_sparse * R_sparse)`

Default weights: `w_lc=1.0`, `w_reg=0.2`, `w_phys=0.1`, `w_sparse=0.25`.

## Evolution Operators
- Population size: `120`
- Elitism: top `8%`
- Selection: tournament (`k=4`)
- Crossover: simulated binary crossover (SBX), probability `p_c=0.85`, distribution index `eta_c=12`
- Mutation:
  - shape genes: Gaussian perturbation, `sigma=0.04`, per-gene probability `p_m=0.08`
  - spin/period genes: Cauchy-jump mutation probability `0.03`
- Constraint repair: clamp shape radii and smooth local spikes with Laplacian projection every generation.

## Stopping Criteria
Stop when any condition is met:
1. Generation reaches `G_max=350`.
2. Best-fitness improvement < `1e-4` over `25` consecutive generations.
3. Validation holdout RMSE worsens by > `3%` for `12` generations (early stopping).

## Notes
The non-convex stage is initialized from convex solution output and allowed to relax convexity penalties gradually (`alpha_convex` annealed from `1.0` to `0.1`) to recover large concavities.

## Citation
- Bartczak & Dudzinski (2018), A&A 611 A47, DOI `10.1051/0004-6361/201731497`.
