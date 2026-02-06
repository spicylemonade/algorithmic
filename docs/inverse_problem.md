# Inverse Problem Formulation (Item 002)

We estimate parameter vector:
\[
\Theta = \{P, \lambda, \beta, \phi_0, \mathbf{s}, \mathbf{q}, \rho\}
\]
where `P` is sidereal period, `(lambda,beta)` ecliptic pole, `phi_0` rotation phase epoch, `s` shape coefficients, `q` scattering parameters, and `rho` optional convexity/concavity controls.

Forward model for calibrated magnitude sample `m_i` at epoch `t_i`:
\[
\hat m_i(\Theta)= m_0 - 2.5\log_{10}(L_i(\Theta) + \epsilon)
\]
\[
L_i = \sum_{f\in\mathcal{V}_i} A_f\,\max(0,\mathbf{n}_f\cdot\mathbf{s}_{\odot,i})\,\max(0,\mathbf{n}_f\cdot\mathbf{s}_{\oplus,i})\,S_f(\alpha_i;\mathbf{q})
\]

Rotation state:
\[
\phi(t_i)=\phi_0 + 2\pi(t_i-t_0)/P
\]
\[
\mathbf{R}_i = \mathbf{R}_z(\lambda)\mathbf{R}_x(\beta)\mathbf{R}_z(\phi(t_i))
\]

Objective (robust, regularized):
\[
\mathcal{L}(\Theta)=\sum_i w_i\,\rho_\delta(m_i-\hat m_i)+\eta_s\|\nabla_{mesh}\mathbf{v}\|_2^2+\eta_c\,\Psi_{concavity}+\eta_p\,\Psi_{physical}
\]
with Huber loss `rho_delta` and regularizers for smoothness/concavity/physical plausibility.

Assumptions:
- Uniform albedo unless explicitly modeled.
- Principal-axis rotation (no tumbling) in baseline pipeline.
- Known ephemeris geometry from MPC/JPL kernels.
- Photometric calibration errors are approximately independent after preprocessing.
- Sparse and dense data are jointly weighted by uncertainty.

## Identifiability Risks for Sparse Photometry
1. Period aliasing from cadence gaps (1-day and synodic aliases).
2. Mirror pole degeneracy (`(lambda,beta)` vs `(lambda+180,-beta)`).
3. Shape-spin coupling causing false elongation under low phase coverage.
4. Phase-angle compression leading to poor concavity observability.
5. Apparition imbalance (one dominant apparition biases pole/period).
6. Calibration offsets between surveys mimic rotational amplitude changes.
7. Unknown albedo variegation confounded with geometric cross-section.
8. Correlated time-system errors (UTC/TDB inconsistencies) shift phase.
9. Underconstrained concavity parameters for <100 sparse points.
10. Outlier contamination from blending/trailing in survey photometry.
