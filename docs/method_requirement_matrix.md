# Method Requirement Matrix (Item 003)

| Capability / Limitation | Kaasalainen-Torppa Convex | SAGE Evolutionary | Durech Sparse Inversion | ADAM Multi-Modal | Planned Module |
|---|---|---|---|---|---|
| 1. Period scan strategy | Coarse-to-fine | Evolves jointly | Sparse-focused grid | Joint modal fit | `lci.period_search` |
| 2. Pole search | Gradient over sphere | Population diversity | Strong prior-driven | Joint optimization | `lci.pole_solver` |
| 3. Convex shape parameterization | Core strength | Seed only | Usually convex | Supports flexible bases | `lci.convex_engine` |
| 4. Non-convex concavities | Limited | Core strength | Weak with sparse data | Supported with additional data | `lci.evo_refine` |
| 5. Regularization | Smoothness essential | Diversity/penalty balancing | Priors critical | Data-type balancing | `lci.losses` |
| 6. Sparse photometry handling | Moderate | Moderate | Core strength | Moderate-to-strong | `lci.sparse_inversion` |
| 7. Multi-source fusion (LC + AO/radar) | Limited | Limited | Limited | Core strength | `lci.data_fusion` |
| 8. Noise robustness | Good with robust residual | Good via population | Sensitive to cadence gaps | Good with joint constraints | `lci.robust_stats` |
| 9. Computational cost | Medium | High | Medium | High | `lci.acceleration` |
| 10. Degeneracy mitigation | Mirror pole remains | Can escape local minima | Prior + apparitions needed | Cross-modal constraints | `lci.uncertainty` |
| 11. Initialization sensitivity | Moderate | High without convex seed | High in low-density data | Moderate | `lci.pipeline` staged flow |
| 12. Physical plausibility constraints | Optional | Must enforce | Optional | Usually enforced | `lci.physics_constraints` |
| 13. Confidence scoring | Not intrinsic | Not intrinsic | Not intrinsic | Emerging practice | `lci.confidence` |
| 14. Survey-era scalability | Historically limited | Expensive | Designed for sparse surveys | Expensive but flexible | `lci.batch_runner` |

## Synthesis Decisions
- Use Kaasalainen-style convex gradient solver as deterministic initializer.
- Use SAGE-like GA only after convex convergence for concavity recovery.
- Use Durech-style sparse priors to stabilize pole/period under low cadence.
- Keep ADAM-inspired interfaces for later multi-modal expansion (AO/radar).
