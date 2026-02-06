# Kaasalainen-Torppa Convex Inversion Synthesis

We parameterize the asteroid shape as a convex polytope with support-function coefficients `s = {s_lm}` on a spherical harmonic basis and spin state `theta = (lambda, beta, P, phi0)`. For observation `i` with geometry `g_i`, model brightness is `L_i(s, theta, q)` where `q` are scattering parameters.

## Objective Function
The baseline optimization target is:

`J = w_lc * sum_i rho((L_i^obs - L_i(s,theta,q))/sigma_i)^2 + w_reg * R_shape(s) + w_spin * R_spin(theta) + w_scat * R_scat(q)`

where:
- `rho(.)` is robust residual shaping (Huber-like) for outlier suppression.
- `R_shape(s) = ||Delta_S s||_2^2 + alpha_c * sum_f max(0, -kappa_f)^2`, combining smoothness and convexity safeguards.
- `R_spin(theta) = ((P-P0)/sigma_P)^2 + gamma * pen_alias(P)`.

## Gradient Updates
For iterative descent step `t`:

`p_t = -B_t^{-1} grad J(x_t)`

`x_{t+1} = x_t + eta_t p_t`

with `x = [s, theta, q]`, `B_t` as Gauss-Newton / L-BFGS approximation, and `eta_t` from backtracking line search that enforces sufficient decrease. For block-coordinate updates:

`grad_s J = -2 w_lc sum_i r_i * (dL_i/ds) + 2 w_reg * Delta_S^T Delta_S s + grad convexity penalties`

`grad_theta J = -2 w_lc sum_i r_i * (dL_i/dtheta) + grad R_spin(theta)`.

## Practical Implementation Constraints
1. Numerical conditioning: the normal matrix in period/pole neighborhoods can become ill-conditioned for sparse phase-angle coverage; damping (`mu I`) and finite-difference gradient checks are mandatory.
2. Scale invariance and mirror poles: purely photometric inversion is insensitive to absolute size and can admit mirror pole solutions; tie-breaking requires cross-apparition geometry and later external constraints.

## Citations
- Kaasalainen & Torppa (2001), Icarus 153, 24-36, DOI: `10.1006/icar.2001.6673`.
- DAMIT reference entry for Kaasalainen & Torppa: https://damit.cuni.cz/projects/damit/references/view/101
- DAMIT overview (Durech et al. 2010), DOI: `10.1051/0004-6361/200912693`.
