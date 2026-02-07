# Non-Convex Evolutionary Strategy (SAGE-Inspired)

## Genome Representation
Each individual encodes:
- `base_shape`: radial coefficients on spherical grid (N=256 directions).
- `concavity_ops`: list of K local deformation primitives (`K<=24`), each:
  - center direction `(lon, lat)`
  - depth `d in [0, 0.4 R]`
  - width `w in [5 deg, 40 deg]`
  - profile exponent `p in [1, 4]`
- Spin parameters: `(lambda, beta, P, phi_0)`.
- Photometric nuisance terms per apparition: `(a_j, b_j)`.

## Initialization
- Seed population from convex-solver outputs plus stochastic concavity perturbations.
- Population size: `N_pop = 96`.
- Fixed RNG seed: `42`.

## Fitness
Minimize composite loss:
`F = w_photo * RMS_photo + w_reg * smooth_penalty + w_phys * self_intersection_penalty + w_sparse * sparse_consistency`

Defaults:
- `w_photo=1.0`, `w_reg=0.08`, `w_phys=10.0`, `w_sparse=0.25`.

## Operators
- Mutation (per gene probability `p_mut=0.15`):
  - Gaussian perturbation on concavity parameters.
  - Random add/remove primitive with `p_add=0.04`, `p_del=0.03`.
  - Pole jitter `(sigma_lon=6 deg, sigma_lat=4 deg)`.
  - Period jitter proportional to current uncertainty (`1e-4 * P`).
- Crossover (`p_cross=0.65`):
  - Uniform crossover on primitives with geometric blending of depths.
  - Arithmetic blend on spin/photometric scalar parameters.

## Selection Policy
- Tournament selection (size 4) to create offspring.
- Elitism: keep best `N_elite=8` unchanged.
- Survivor strategy: `(mu+lambda)` with `mu=96`, `lambda=192`.
- Diversity guard: reject offspring with mesh similarity > 0.98 to elites.

## Stop Criteria
Terminate if any condition holds:
- `gen >= 300`.
- Best fitness improvement `< 1e-4` over 40 generations.
- Population diversity metric `< 0.02` and improvement plateaued for 25 generations.

## Output
- Best non-convex mesh
- Ensemble of top-10 solutions for uncertainty estimation
- Convergence trace (fitness vs generation)
