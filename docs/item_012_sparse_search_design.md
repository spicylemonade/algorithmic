# Sparse-Aware Pole and Period Search

Implemented in `src/lci/sparse_solver.py`:
- Multi-resolution period scan:
  - coarse grid step `0.05 h`
  - fine refinement step `0.005 h` around top coarse minima
- Pole sampling strategy:
  - Fibonacci-sphere ecliptic sampling, default `1024` samples
- Ambiguity resolution:
  - choose best-posterior pole when score margin exceeds `0.03`
  - near-ties fall back to hemisphere-consistency rule (proxy for multi-apparition consistency)

Design target supports sparse datasets with `<= 100` points by relying on binned phase statistics and ambiguity scoring rather than overfitted dense-shape gradients.
