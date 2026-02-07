# Convex Inversion Mathematical Requirements (Kaasalainen-Torppa Synthesis)

## Shape Parameterization
- Represent asteroid as a star-convex radial function on fixed directions `u_k`:
  - `r_k = exp(s_k)` for positivity.
  - Vertex positions: `v_k = r_k * u_k`.
- Spin state parameters:
  - Pole longitude/latitude: `(lambda, beta)`.
  - Sidereal period: `P`.
  - Initial rotational phase: `phi_0`.
- Photometric scale parameters per apparition: `a_j`, optional offset `b_j`.

## Forward Model
For observation `i` with geometry `(s_i, e_i, t_i)`:
1. Compute rotational phase `phi_i = phi_0 + 2*pi*(t_i - t_ref)/P`.
2. Rotate shape into inertial frame from pole `(lambda, beta, phi_i)`.
3. Evaluate illuminated-visible facet set and scattering response.
4. Predicted brightness `L_hat_i = a_app(i) * Sum_f (A_f * mu0_f * mu_f * S_f) + b_app(i)`.

## Objective Function
Minimize

`J(theta) = w_data * J_data + w_smooth * J_smooth + w_conv * J_conv + w_spin * J_spin`

where `theta = {s_k, lambda, beta, P, phi_0, a_j, b_j}`.

- Data term (robust least squares):
  - `J_data = Sum_i rho((L_i - L_hat_i)/sigma_i)^2`, with Huber `rho`.
- Smoothness regularization (Laplacian on log-radii):
  - `J_smooth = ||L*s||_2^2`.
- Convexity regularization (local support consistency):
  - `J_conv = Sum_(triangles) max(0, -n_f dot c_f)^2`.
- Spin prior term (optional):
  - `J_spin = ((P-P0)/sP)^2 + ((beta-beta0)/sb)^2`.

## Gradients
Using chain rule:

- `dJ/ds_k = -2*w_data*Sum_i r_i*(dL_hat_i/ds_k) + 2*w_smooth*(L^T L s)_k + dJ_conv/ds_k`
- `dJ/dP = -2*w_data*Sum_i r_i*(dL_hat_i/dphi_i)*(dphi_i/dP) + 2*w_spin*(P-P0)/sP^2`
- `dphi_i/dP = -2*pi*(t_i - t_ref)/P^2`
- `dJ/dlambda, dJ/dbeta, dJ/dphi_0` derived from rotation Jacobian and photometric Jacobian.

`r_i = rho'((L_i-L_hat_i)/sigma_i) / sigma_i`.

## Optimization Defaults
- Optimizer: projected L-BFGS with backtracking line search.
- Initialize from triaxial ellipsoid and coarse period grid.
- Stop criteria:
  - relative objective improvement `< 1e-6` over 20 steps, or
  - gradient norm `< 1e-5`, or
  - max iterations `= 2000`.

## Determinism
- Seed fixed to `42` for randomized starts.
- Deterministic ordering of observations/facets.
