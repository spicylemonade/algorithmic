# Sparse Inversion Module (Item 012)

Algorithm:
1. Enforce minimum operating envelope: `>=100` sparse points and `>=3` apparitions.
2. Perform regularized coarse grid search over period and pole.
3. Optimize objective composed of:
- sparse photometric RMS term,
- period prior penalty,
- pole prior penalty,
- smoothness regularizer.
4. Output best period/pole candidate with objective score.

Priors and regularization:
- Gaussian-like period prior (`sigma=0.5 hr` around weak nominal center).
- Pole-latitude shrinkage toward physically plausible orientations.
- Mild smoothness penalty to avoid unstable pole oscillations.

Minimum-data envelope:
- Below operating envelope, module fails fast with explicit error.
