# Adaptive Multi-objective Loss (Item 013)

Loss components:
- `photo`: photometric fit residual.
- `smooth`: mesh smoothness regularization.
- `physical`: physical plausibility penalties (spin/shape).
- `concavity`: concavity-specific penalty or reward shaping.

Weighted objective:
`L = w_photo*photo + w_smooth*smooth + w_physical*physical + w_concavity*concavity`

Adaptive update bands:
- High error (`val_error > 0.08`): emphasize photometric + concavity terms.
- Medium error (`0.04 < val_error <= 0.08`): mild photo increase + stronger physical term.
- Low error (`<=0.04`): increase regularization/physical terms for stability.

After updates, weights are normalized to sum to 1.
