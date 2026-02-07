# Method Traceability: Literature to Implementation

## Source Set
- Kaasalainen et al. (2001), Optimization methods for asteroid lightcurve inversion.
- Bartczak & Dudzinski (2018), SAGE.
- Durech et al. (2010), Asteroid models from sparse photometry.
- Viikinkoski et al. (2015), ADAM.

## Traceability Table
| ID | Equation / Algorithmic Element | Source Section | Implementation Module |
|---|---|---|---|
| T1 | Weighted least squares lightcurve objective `sum w_i (m_obs - m_model)^2` | Kaasalainen 2001, optimization objective sections | `lci.convex_optimizer` |
| T2 | Regularized inverse problem with smoothness term `lambda R(shape)` | Kaasalainen 2001, regularization treatment | `lci.convex_optimizer`, `lci.priors` |
| T3 | Convex polytope support-function parameterization | Kaasalainen 2001, convex representation | `lci.geometry` |
| T4 | Gradient descent / quasi-Newton style parameter update | Kaasalainen 2001, minimization workflow | `lci.convex_optimizer` |
| T5 | Rotation phase model `phi(t)=phi0+2pi/P*(t-t0)` | Kaasalainen 2001 + Durech 2010 period search context | `lci.photometry`, `lci.orbits` |
| T6 | Sparse cadence weighting and apparition balancing | Durech 2010, sparse-data inversion strategy | `lci.sparse_solver`, `lci.hybrid_optimizer` |
| T7 | Multi-start pole search over sphere discretization | Durech 2010, pole ambiguity handling | `lci.sparse_solver` |
| T8 | Genetic chromosome for non-convex control points | Bartczak 2018, genotype parameterization | `lci.evolutionary` |
| T9 | Evolution operators: mutation, crossover, selection | Bartczak 2018, GA loop | `lci.evolutionary` |
| T10 | Fitness as photometric residual plus shape penalties | Bartczak 2018, objective definition | `lci.evolutionary`, `lci.priors` |
| T11 | Multi-data fusion objective (photometry + shape constraints) | Viikinkoski 2015, ADAM objective composition | `lci.hybrid_optimizer`, `lci.metrics` |
| T12 | Scale/pose-invariant mesh comparison (distance fields / overlap) | Viikinkoski 2015 validation practice | `lci.metrics` |
| T13 | Bootstrap/multistart confidence region estimation | Durech 2010 uncertainty discussion + ADAM practice | `lci.uncertainty` |
| T14 | Physical plausibility prior for inertia and spin | Viikinkoski 2015 physically constrained inversion | `lci.priors` |

## Synthesis Notes
- Convex inversion is used as stable initialization for sparse and dense data.
- Evolutionary non-convex search is scheduled after convex convergence to recover large concavities.
- Sparse-data robustness is achieved via weighted objective balancing and restart strategy.
- Validation metrics include both photometric fit and geometric truth-match metrics.
