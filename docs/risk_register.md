# Risk Register and Roadmap (Item 025)

| Risk ID | Risk | Owner | Status | Mitigation | Follow-up Experiment |
|---|---|---|---|---|---|
| R1 | Sparse cadence period aliasing | Signal Lead | Open | Multi-apparition weighted period grid | Alias stress sweep with injected cadence gaps |
| R2 | Mirror-pole degeneracy | Dynamics Lead | Open | Hemisphere prior + geometry diversity | Pole disambiguation with synthetic mirrored twins |
| R3 | Survey cross-calibration drift | Data Lead | Open | Per-source zeropoint offsets | Joint fit with withheld-survey validation |
| R4 | Albedo-shape confounding | Physics Lead | Open | Add albedo nuisance parameters | Recover shape under controlled albedo patterns |
| R5 | Non-convex overfitting | Optimization Lead | Open | Concavity regularization + early stop | GA ablation over mutation/crossover schedule |
| R6 | Runtime blow-up at scale | Performance Lead | Open | C++ kernels for heavy linear algebra | Profile-driven benchmark on 1k-object batch |
| R7 | Mesh quality artifacts | Geometry Lead | Open | Mesh Laplacian smoothing constraint | Evaluate self-intersection and normal consistency |
| R8 | Incomplete Itokawa-like sparse data | Data Lead | Open | PDS + survey fusion fallback | Robustness test under missing phase windows |
| R9 | Confidence miscalibration | UQ Lead | Open | Bootstrap calibration by bins | Reliability diagram vs empirical pass rates |
| R10 | Baseline comparison mismatch | Validation Lead | Open | Standardized metric protocol | Recompute baselines on identical test split |
| R11 | Licensing/provenance ambiguity | Release Lead | Open | Artifact-level provenance metadata | Audit release bundle for missing citations |
| R12 | Hidden numerical instability | QA Lead | Open | Tight tolerances + consistency tests | Long-run deterministic replay across commits |

Roadmap sequence:
1. Resolve R1-R5 (model correctness risks).
2. Resolve R6-R8 (scalability/data completeness).
3. Resolve R9-R12 (validation/release hardening).
