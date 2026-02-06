# Forward Research Roadmap

1. Integrate true LCDB machine-readable ingestion
- Impact: High
- Effort: Medium
- Dependencies: stable LCDB endpoint access

2. Replace bbox IoU with voxelized mesh IoU
- Impact: High
- Effort: Medium
- Dependencies: mesh voxelization module

3. Add C++ brightness/gradient kernels
- Impact: High
- Effort: High
- Dependencies: pybind11 build scaffolding

4. Full adaptive-loop integration in benchmark driver
- Impact: High
- Effort: Medium
- Dependencies: reinforcement module wiring

5. Add uncertainty-aware Bayesian pole posterior
- Impact: Medium
- Effort: Medium
- Dependencies: sparse solver refactor

6. Multi-survey photometric calibration solver
- Impact: High
- Effort: High
- Dependencies: robust per-survey metadata ingest

7. Incorporate occultation/AO fusion (ADAM-like)
- Impact: Medium
- Effort: High
- Dependencies: additional data connectors

8. Implement distributed GA evaluation backend
- Impact: Medium
- Effort: Medium
- Dependencies: multiprocessing/job queue runtime

9. Expand validation set beyond 10 objects with mission-grade meshes
- Impact: High
- Effort: Medium
- Dependencies: additional curated ground truth data

10. Confidence calibration against held-out truth labels
- Impact: High
- Effort: Medium
- Dependencies: larger labeled validation corpus
