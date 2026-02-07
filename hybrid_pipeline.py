"""
Hybrid Convex-to-Nonconvex Pipeline (Module 9)

Combines the convex inversion solver (Kaasalainen-Torppa) with the
evolutionary/genetic solver (SAGE-style) in a two-stage pipeline:

1. Stage 1 — Convex inversion to recover pole, period, and convex shape.
2. Stage 2 — If residual chi-squared exceeds a threshold, seed the
   evolutionary solver with the convex solution and refine towards a
   non-convex shape.

References:
    Kaasalainen & Torppa (2001) — convex inversion
    Bartczak & Dudzinski (2018) — SAGE evolutionary refinement
    Viikinkoski et al. (2015) — multi-stage inversion (ADAM)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

from forward_model import (TriMesh, create_sphere_mesh, compute_face_properties,
                           save_obj)
from geometry import SpinState
from convex_solver import (LightcurveData, InversionResult, run_convex_inversion,
                           optimize_shape, chi_squared)
from genetic_solver import (GAConfig, GAResult, run_genetic_solver,
                            create_dumbbell_mesh)


@dataclass
class HybridConfig:
    """Configuration for the hybrid pipeline."""
    # Convex stage
    n_periods: int = 50
    n_lambda: int = 12
    n_beta: int = 6
    n_subdivisions: int = 2
    c_lambert: float = 0.1
    reg_weight_convex: float = 0.01
    max_shape_iter: int = 200

    # Adaptive switch threshold
    chi2_threshold: float = 0.05

    # Evolutionary stage
    ga_population: int = 50
    ga_generations: int = 300
    ga_tournament: int = 5
    ga_elite_fraction: float = 0.1
    ga_mutation_rate: float = 0.9
    ga_mutation_sigma: float = 0.05
    ga_crossover_rate: float = 0.6
    ga_reg_weight: float = 0.001
    ga_seed: int = 42

    verbose: bool = False


@dataclass
class HybridResult:
    """Result of the hybrid pipeline."""
    mesh: TriMesh
    spin: SpinState
    chi_squared_convex: float
    chi_squared_final: float
    used_ga: bool
    convex_result: Optional[InversionResult] = None
    ga_result: Optional[GAResult] = None
    stage: str = "convex"


def run_hybrid_pipeline(lightcurves, p_min, p_max, config=None):
    """Run the full hybrid convex -> evolutionary pipeline.

    Parameters
    ----------
    lightcurves : list of LightcurveData
        Observed lightcurves.
    p_min, p_max : float
        Period search range (hours).
    config : HybridConfig, optional
        Pipeline configuration. Uses defaults if None.

    Returns
    -------
    HybridResult
        Final shape model and diagnostics.
    """
    if config is None:
        config = HybridConfig()

    # === Stage 1: Convex inversion ===
    if config.verbose:
        print("=" * 50)
        print("STAGE 1: Convex Inversion")
        print("=" * 50)

    convex_result = run_convex_inversion(
        lightcurves,
        p_min=p_min,
        p_max=p_max,
        n_periods=config.n_periods,
        n_lambda=config.n_lambda,
        n_beta=config.n_beta,
        n_subdivisions=config.n_subdivisions,
        c_lambert=config.c_lambert,
        reg_weight=config.reg_weight_convex,
        max_shape_iter=config.max_shape_iter,
        verbose=config.verbose,
    )

    chi2_convex = convex_result.chi_squared
    if config.verbose:
        print(f"\nConvex chi-squared: {chi2_convex:.6f}")
        print(f"Threshold:         {config.chi2_threshold:.6f}")

    # === Decision: do we need non-convex refinement? ===
    if chi2_convex <= config.chi2_threshold:
        if config.verbose:
            print("\nConvex solution meets threshold — skipping GA stage.")
        return HybridResult(
            mesh=convex_result.mesh,
            spin=convex_result.spin,
            chi_squared_convex=chi2_convex,
            chi_squared_final=chi2_convex,
            used_ga=False,
            convex_result=convex_result,
            stage="convex",
        )

    # === Stage 2: Evolutionary refinement ===
    if config.verbose:
        print("\n" + "=" * 50)
        print("STAGE 2: Evolutionary Refinement (GA)")
        print("=" * 50)

    ga_config = GAConfig(
        population_size=config.ga_population,
        n_generations=config.ga_generations,
        tournament_size=config.ga_tournament,
        elite_fraction=config.ga_elite_fraction,
        mutation_rate=config.ga_mutation_rate,
        mutation_sigma=config.ga_mutation_sigma,
        mutation_sigma_decay=0.998,
        crossover_rate=config.ga_crossover_rate,
        c_lambert=config.c_lambert,
        reg_weight=config.ga_reg_weight,
        seed=config.ga_seed,
        verbose=config.verbose,
    )

    # Seed GA with the convex solution
    ga_result = run_genetic_solver(
        lightcurves,
        spin=convex_result.spin,
        config=ga_config,
        initial_mesh=convex_result.mesh,
    )

    chi2_ga = ga_result.fitness
    if config.verbose:
        print(f"\nGA final fitness: {chi2_ga:.6f}")

    # Pick the better solution
    if chi2_ga < chi2_convex:
        final_mesh = ga_result.mesh
        final_chi2 = chi2_ga
        stage = "ga"
    else:
        final_mesh = convex_result.mesh
        final_chi2 = chi2_convex
        stage = "convex"

    return HybridResult(
        mesh=final_mesh,
        spin=convex_result.spin,
        chi_squared_convex=chi2_convex,
        chi_squared_final=final_chi2,
        used_ga=True,
        convex_result=convex_result,
        ga_result=ga_result,
        stage=stage,
    )


def run_hybrid_with_known_spin(lightcurves, spin, config=None):
    """Run hybrid pipeline with known spin (skip period/pole search).

    Useful when spin is already determined (e.g., from literature).

    Parameters
    ----------
    lightcurves : list of LightcurveData
    spin : SpinState
        Known spin state.
    config : HybridConfig, optional

    Returns
    -------
    HybridResult
    """
    if config is None:
        config = HybridConfig()

    # === Stage 1: Convex shape optimization at known spin ===
    if config.verbose:
        print("=" * 50)
        print("STAGE 1: Convex Shape Optimization (known spin)")
        print("=" * 50)

    initial_mesh = create_sphere_mesh(config.n_subdivisions)
    opt_mesh, chi2_convex, history = optimize_shape(
        initial_mesh, spin, lightcurves,
        c_lambert=config.c_lambert,
        reg_weight=config.reg_weight_convex,
        max_iter=config.max_shape_iter,
        verbose=config.verbose,
    )

    convex_result = InversionResult(
        mesh=opt_mesh, spin=spin, chi_squared=chi2_convex,
        chi_squared_history=history
    )

    if config.verbose:
        print(f"\nConvex chi-squared: {chi2_convex:.6f}")
        print(f"Threshold:         {config.chi2_threshold:.6f}")

    if chi2_convex <= config.chi2_threshold:
        if config.verbose:
            print("\nConvex solution meets threshold — skipping GA stage.")
        return HybridResult(
            mesh=opt_mesh, spin=spin,
            chi_squared_convex=chi2_convex,
            chi_squared_final=chi2_convex,
            used_ga=False,
            convex_result=convex_result,
            stage="convex",
        )

    # === Stage 2: GA refinement ===
    if config.verbose:
        print("\n" + "=" * 50)
        print("STAGE 2: Evolutionary Refinement (GA)")
        print("=" * 50)

    ga_config = GAConfig(
        population_size=config.ga_population,
        n_generations=config.ga_generations,
        tournament_size=config.ga_tournament,
        elite_fraction=config.ga_elite_fraction,
        mutation_rate=config.ga_mutation_rate,
        mutation_sigma=config.ga_mutation_sigma,
        mutation_sigma_decay=0.998,
        crossover_rate=config.ga_crossover_rate,
        c_lambert=config.c_lambert,
        reg_weight=config.ga_reg_weight,
        seed=config.ga_seed,
        verbose=config.verbose,
    )

    ga_result = run_genetic_solver(
        lightcurves, spin=spin, config=ga_config, initial_mesh=opt_mesh,
    )

    chi2_ga = ga_result.fitness
    if chi2_ga < chi2_convex:
        final_mesh = ga_result.mesh
        final_chi2 = chi2_ga
        stage = "ga"
    else:
        final_mesh = opt_mesh
        final_chi2 = chi2_convex
        stage = "convex"

    return HybridResult(
        mesh=final_mesh, spin=spin,
        chi_squared_convex=chi2_convex,
        chi_squared_final=final_chi2,
        used_ga=True,
        convex_result=convex_result,
        ga_result=ga_result,
        stage=stage,
    )
