# Baseline Optimization and Regularization Parameters

| Parameter | Module | Default | Range | Rationale |
|---|---|---:|---|---|
| `convex_lr` | convex | 0.05 | 0.005-0.2 | Stable descent on noisy lightcurve objective |
| `convex_iters` | convex | 120 | 50-500 | Enough updates before GA handoff |
| `convex_fd_eps` | convex | 1e-3 | 1e-4-1e-2 | Finite-difference balance noise vs bias |
| `convex_w_misfit` | convex | 1.0 | 0.5-3.0 | Data term should dominate |
| `convex_w_smooth` | convex | 0.02 | 1e-4-0.2 | Kaasalainen-style regularization |
| `convex_w_convexity` | convex | 0.4 | 0.05-2.0 | Prevent self-intersections in init |
| `period_init_h` | convex/sparse | 4.0 | 2.0-20.0 | Typical asteroid period prior |
| `period_grid_coarse_h` | sparse | 0.05 | 0.01-0.2 | Alias-resolving coarse scan |
| `period_grid_fine_h` | sparse | 0.005 | 0.001-0.02 | Local refinement around minima |
| `pole_samples` | sparse | 2048 | 256-8192 | S2 coverage tradeoff |
| `ga_population` | evolutionary | 120 | 40-400 | SAGE-like diversity requirement |
| `ga_elite_fraction` | evolutionary | 0.08 | 0.02-0.2 | Preserve top hypotheses |
| `ga_crossover_prob` | evolutionary | 0.85 | 0.6-0.95 | Mix structural traits efficiently |
| `ga_mutation_prob` | evolutionary | 0.08 | 0.01-0.2 | Escape local minima |
| `ga_mut_sigma` | evolutionary | 0.04 | 0.005-0.15 | Geometry perturbation scale |
| `ga_generations` | evolutionary | 350 | 50-1000 | Convergence for non-convex stage |
| `ga_plateau_window` | evolutionary | 25 | 10-80 | Early plateau detection |
| `w_sparse` | fused loss | 0.25 | 0.05-1.0 | Lift sparse constraints under low cadence |
| `w_phys` | fused loss | 0.1 | 0.01-0.8 | Enforce physical plausibility |
| `adaptive_retry_max` | reinforcement | 5 | 1-12 | Bound self-reinforcement loops |
| `acceptance_deviation` | validation | 0.05 | fixed | Project criterion for pass/fail |

Default values are centered on conservative convex stabilization and moderate GA exploration, consistent with Kaasalainen-style regularization and SAGE-like refinement strategy.
