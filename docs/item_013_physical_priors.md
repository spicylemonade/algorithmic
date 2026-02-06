# Physically Informed Priors and Constraints

Implemented penalties (`src/lci/priors.py`):
1. Spin-state consistency: `P_spin = max(0, (Δaxis - τ_axis)/τ_axis)^2`
2. Inertia plausibility: `P_inertia = max(0, (axis_ratio-r_max)/r_max)^2`
3. Convexity relaxation bound: `P_conc = max(0, (f_conc-b_conc)/b_conc)^2`
4. Albedo/phase behavior: bounded phase slope penalty
5. Spin-rate physical range penalty (`P < 2.1h` heavily penalized)
6. Density proxy penalty from `omega^2 * V^(1/3)` range

Aggregate regularizer:
`R_phys = sum_k w_k P_k`

This provides >=6 physically motivated constraints with explicit mathematical forms.
