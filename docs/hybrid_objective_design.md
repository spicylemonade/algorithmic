# Hybrid Objective: Convex + Non-Convex Priors

Composite loss at optimization stage `k`:

`L_k = w_photo(k)*R_photo + w_smooth(k)*R_smooth + w_concavity(k)*R_concavity`

Where:
- `R_photo`: weighted photometric residual term.
- `R_smooth`: mesh smoothness/Laplacian penalty.
- `R_concavity`: concavity prior encouraging plausible non-convex features while penalizing pathological artifacts.

Adaptive weight schedule:
- Stage 0 (convex bootstrap): `w_photo=1.0, w_smooth=0.35, w_concavity=0.02`
- Stage 1 (transition): `w_photo=1.0, w_smooth=0.20, w_concavity=0.12`
- Stage 2 (non-convex refinement): `w_photo=1.0, w_smooth=0.12, w_concavity=0.25`

Rationale:
- Early stages enforce smooth convex stability.
- Later stages relax smoothness and increase concavity prior to recover large-scale depressions/bifurcations.

Implementation: `src/lci/hybrid_objective.py`.
