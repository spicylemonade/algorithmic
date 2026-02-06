"""Physical regularization terms for shape/spin optimization."""

from __future__ import annotations


def inertia_alignment_penalty(spin_axis, principal_axis):
    return 1.0 - sum(a * b for a, b in zip(spin_axis, principal_axis)) ** 2


def spin_state_consistency_penalty(period_h, period_prior_h, sigma_h=0.5):
    return ((period_h - period_prior_h) / max(sigma_h, 1e-6)) ** 2


def mesh_smoothness_penalty(laplacian_norm):
    return laplacian_norm**2


def concavity_preservation_gate(local_curvature, threshold=0.25):
    # Reduce smoothing on strong concavity features.
    return 0.2 if local_curvature > threshold else 1.0


def total_regularization(spin_axis, principal_axis, period_h, period_prior_h, laplacian_norm, local_curvature):
    w_inertia = 0.4
    w_spin = 0.3
    w_smooth = 0.3 * concavity_preservation_gate(local_curvature)
    return (
        w_inertia * inertia_alignment_penalty(spin_axis, principal_axis)
        + w_spin * spin_state_consistency_penalty(period_h, period_prior_h)
        + w_smooth * mesh_smoothness_penalty(laplacian_norm)
    )
