# Technical Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Sparse photometry degeneracy causes pole ambiguity | High | High | Mirror-pole branch retention + multi-apparition tie-breakers | Inversion Lead |
| R2 | Overfitting non-convex concavities to noise | Medium | High | Concavity regularization schedule + rollback policy | Optimization Lead |
| R3 | Period aliasing in sparse mode | High | High | Coarse-to-fine multi-resolution period scan | Sparse Module Owner |
| R4 | Data-quality heterogeneity across surveys | High | Medium | Source-specific parse/quality gates and outlier rejection | Ingestion Lead |
| R5 | Incompatible timestamp/epoch standards | Medium | High | Canonical JD normalization and provenance tagging | Geometry Lead |
| R6 | Missing/closed-source baseline tools for SOTA comparison | High | Medium | Document partial benchmark and failure mode transparently | Evaluation Lead |
| R7 | Runtime cost for large candidate scans | High | Medium | Deferred DAMIT calls, batching, and capped pool runs | Pipeline Lead |
| R8 | DAMIT availability uncertainty/format changes | Medium | Medium | Robust HTTP parsing with fallback indicators | Data Ops |
| R9 | Confidence intervals underrepresent model uncertainty | Medium | Medium | Multi-start ensembles + conservative 95% bounds | UQ Lead |
| R10 | Inadequate candidate coverage for exact top-50 | High | High | Extend harvest runtime and broaden source joins | Targeting Lead |
| R11 | Validation metric mismatch vs external tools | Medium | Medium | Exact formula documentation + implementation tests | Validation Lead |
| R12 | Artifact provenance loss during packaging | Low | High | Mandatory provenance manifest and checksum policy | Release Lead |
