# Reproducibility Protocol

Run manifest captures:
- dataset hashes
- random seed (`42`)
- software module list
- Python/runtime platform
- timestamp and package version

Pilot determinism procedure:
1. Run `run_pilot(seed=42)` twice.
2. Compare key metrics (`period_evo`, `loss_evo`) across reruns.
3. Compute relative variance = `abs(run1-run2)/max(abs(run1),1e-12)`.
4. Pass criterion: variance <= 1%.
