#!/usr/bin/env python3
"""
Enhanced Hyperparameter Optimization for 3D Planetary Gravity Simulation
Explores extended parameter space with adaptive timesteps and additional metrics
"""

import numpy as np
import json
import os
from main import create_solar_system_inner, CelestialBody
from hyperparameter_optimization import OptimizedGravitySimulation


class AdaptiveGravitySimulation(OptimizedGravitySimulation):
    """Simulation with adaptive timestep control."""

    def __init__(self, bodies, dt=1000.0, softening=0.0, integration_method='verlet',
                 adaptive_dt=False, dt_tolerance=1e-3):
        """
        Initialize simulation with adaptive timestep.

        Args:
            bodies: List of CelestialBody objects
            dt: Base time step in seconds
            softening: Softening parameter
            integration_method: Integration method
            adaptive_dt: Enable adaptive timestep
            dt_tolerance: Tolerance for adaptive timestep adjustment
        """
        super().__init__(bodies, dt, softening, integration_method)
        self.adaptive_dt = adaptive_dt
        self.dt_tolerance = dt_tolerance
        self.base_dt = dt
        self.dt_adjustments = 0

    def estimate_error(self):
        """Estimate local truncation error using half-step method."""
        if not self.adaptive_dt:
            return 0.0

        # Save current state
        positions = [b.position.copy() for b in self.bodies]
        velocities = [b.velocity.copy() for b in self.bodies]

        # Take one full step
        old_dt = self.dt
        self.step()
        full_step_positions = [b.position.copy() for b in self.bodies]

        # Reset and take two half steps
        for i, body in enumerate(self.bodies):
            body.position = positions[i].copy()
            body.velocity = velocities[i].copy()

        self.dt = old_dt / 2
        self.step()
        self.step()
        half_step_positions = [b.position.copy() for b in self.bodies]

        # Estimate error
        max_error = 0.0
        for i in range(len(self.bodies)):
            error = np.linalg.norm(full_step_positions[i] - half_step_positions[i])
            max_error = max(max_error, error)

        # Keep the half-step result (more accurate)
        self.dt = old_dt
        return max_error

    def run_adaptive(self, num_steps):
        """Run simulation with adaptive timestep control."""
        for _ in range(num_steps):
            if self.adaptive_dt:
                error = self.estimate_error()

                # Adjust timestep based on error
                if error > self.dt_tolerance:
                    self.dt = max(self.base_dt * 0.5, self.dt * 0.9)
                    self.dt_adjustments += 1
                elif error < self.dt_tolerance * 0.1:
                    self.dt = min(self.base_dt * 2.0, self.dt * 1.1)
            else:
                self.step()

            self.energy_history.append(self.calculate_total_energy())


def evaluate_config_extended(dt, softening, integration_method,
                            adaptive_dt=False, num_steps=1000):
    """
    Evaluate configuration with extended metrics.

    Returns:
        dict: Comprehensive metrics
    """
    bodies = create_solar_system_inner()

    sim = AdaptiveGravitySimulation(
        bodies,
        dt=dt,
        softening=softening,
        integration_method=integration_method,
        adaptive_dt=adaptive_dt
    )

    # Initial conditions
    initial_energy = sim.calculate_total_energy()
    initial_momentum = sim.calculate_momentum()

    # Track distances for orbit stability
    initial_distances = []
    for body in bodies[1:]:  # Skip sun
        dist = np.linalg.norm(body.position - bodies[0].position)
        initial_distances.append(dist)

    # Run simulation
    if adaptive_dt:
        sim.run_adaptive(num_steps)
    else:
        sim.run(num_steps)

    # Final measurements
    final_energy = sim.calculate_total_energy()
    final_momentum = sim.calculate_momentum()

    # Check orbit stability
    final_distances = []
    for body in sim.bodies[1:]:
        dist = np.linalg.norm(body.position - sim.bodies[0].position)
        final_distances.append(dist)

    # Calculate orbit deviation (should remain roughly constant)
    orbit_deviations = []
    for i, (init_d, final_d) in enumerate(zip(initial_distances, final_distances)):
        deviation = abs(final_d - init_d) / init_d * 100
        orbit_deviations.append(deviation)

    avg_orbit_deviation = np.mean(orbit_deviations)

    # Energy conservation
    energy_error = abs((final_energy - initial_energy) / initial_energy) * 100
    momentum_error = abs((final_momentum - initial_momentum) / max(initial_momentum, 1e-10)) * 100

    # Check validity
    is_valid = not (np.isnan(final_energy) or np.isinf(final_energy) or
                   np.isnan(final_momentum) or np.isinf(final_momentum) or
                   any(np.isnan(d) for d in final_distances))

    # Energy drift over time (should be minimal)
    energy_drift = 0.0
    if len(sim.energy_history) > 1:
        energy_changes = np.diff(sim.energy_history)
        energy_drift = np.std(energy_changes) / abs(initial_energy) * 100

    # Scoring
    energy_score = max(0, 100 - energy_error * 10) if is_valid else 0
    momentum_score = max(0, 100 - momentum_error * 10) if is_valid else 0
    orbit_stability_score = max(0, 100 - avg_orbit_deviation * 2) if is_valid else 0
    energy_drift_score = max(0, 100 - energy_drift * 100) if is_valid else 0

    # Weighted overall score (energy conservation most important)
    overall_score = (
        0.40 * energy_score +
        0.25 * momentum_score +
        0.20 * orbit_stability_score +
        0.15 * energy_drift_score
    ) if is_valid else 0

    return {
        'dt': dt,
        'softening': softening,
        'integration_method': integration_method,
        'adaptive_dt': adaptive_dt,
        'num_steps': num_steps,
        'energy_error': energy_error if is_valid else float('inf'),
        'momentum_error': momentum_error if is_valid else float('inf'),
        'orbit_deviation': avg_orbit_deviation if is_valid else float('inf'),
        'energy_drift': energy_drift if is_valid else float('inf'),
        'energy_score': energy_score,
        'momentum_score': momentum_score,
        'orbit_stability_score': orbit_stability_score,
        'energy_drift_score': energy_drift_score,
        'overall_score': overall_score,
        'is_valid': is_valid,
        'simulation_time_days': num_steps * dt / (24 * 3600),
        'dt_adjustments': getattr(sim, 'dt_adjustments', 0)
    }


def focused_hyperparameter_search():
    """
    Perform focused search around best known configurations.
    """
    print("=" * 80)
    print("ENHANCED HYPERPARAMETER OPTIMIZATION - 3D PLANETARY GRAVITY SIMULATION")
    print("=" * 80)

    # Expanded search space focused on promising regions
    dt_values = [
        1800,   # 0.5 hours
        2700,   # 0.75 hours
        3600,   # 1 hour (known good)
        5400,   # 1.5 hours
        7200,   # 2 hours
    ]

    softening_values = [
        0.0,      # No softening (pure N-body)
        1e7,      # Small softening
        5e7,      # Medium softening
        1e8,      # Larger softening
    ]

    integration_methods = [
        'verlet',  # Good balance
        'rk4',     # Most accurate (previous winner)
    ]

    adaptive_dt_values = [False, True]  # Test adaptive timestep

    num_steps = 1000

    print(f"\nExpanded search space:")
    print(f"  dt: {dt_values} seconds")
    print(f"  softening: {softening_values} meters")
    print(f"  integration_method: {integration_methods}")
    print(f"  adaptive_dt: {adaptive_dt_values}")
    print(f"  num_steps: {num_steps}")

    total_configs = (len(dt_values) * len(softening_values) *
                    len(integration_methods) * len(adaptive_dt_values))
    print(f"\nTotal configurations: {total_configs}")

    # Run experiments
    results = []
    current = 0

    print("\n" + "=" * 80)
    print("Running experiments...")
    print("=" * 80)

    for dt in dt_values:
        for softening in softening_values:
            for method in integration_methods:
                for adaptive in adaptive_dt_values:
                    current += 1
                    config_str = f"dt={dt}s, soft={softening:.0e}m, method={method}, adaptive={adaptive}"
                    print(f"\n[{current}/{total_configs}] Testing: {config_str}")

                    try:
                        result = evaluate_config_extended(
                            dt, softening, method, adaptive, num_steps
                        )
                        results.append(result)

                        print(f"  Energy error: {result['energy_error']:.6f}%")
                        print(f"  Momentum error: {result['momentum_error']:.6f}%")
                        print(f"  Orbit deviation: {result['orbit_deviation']:.4f}%")
                        print(f"  Energy drift: {result['energy_drift']:.6f}%")
                        print(f"  Overall score: {result['overall_score']:.2f}/100")

                    except Exception as e:
                        print(f"  ERROR: {e}")
                        results.append({
                            'dt': dt,
                            'softening': softening,
                            'integration_method': method,
                            'adaptive_dt': adaptive,
                            'overall_score': 0.0,
                            'is_valid': False,
                            'error': str(e)
                        })

    # Analyze results
    valid_results = [r for r in results if r.get('is_valid', False)]

    if not valid_results:
        print("\nERROR: No valid configurations found!")
        return None, results

    best_result = max(valid_results, key=lambda x: x['overall_score'])

    print("\n" + "=" * 80)
    print("OPTIMIZATION RESULTS")
    print("=" * 80)

    print(f"\nBest configuration:")
    print(f"  Time step: {best_result['dt']} seconds ({best_result['dt']/3600:.2f} hours)")
    print(f"  Softening: {best_result['softening']:.2e} meters")
    print(f"  Integration method: {best_result['integration_method']}")
    print(f"  Adaptive timestep: {best_result['adaptive_dt']}")

    print(f"\nDetailed performance metrics:")
    print(f"  Overall score: {best_result['overall_score']:.2f}/100")
    print(f"  Energy conservation error: {best_result['energy_error']:.6f}%")
    print(f"  Momentum conservation error: {best_result['momentum_error']:.6f}%")
    print(f"  Average orbit deviation: {best_result['orbit_deviation']:.4f}%")
    print(f"  Energy drift: {best_result['energy_drift']:.6f}%")
    print(f"  Simulation duration: {best_result['simulation_time_days']:.1f} days")

    print(f"\nComponent scores:")
    print(f"  Energy score: {best_result['energy_score']:.2f}/100 (weight: 40%)")
    print(f"  Momentum score: {best_result['momentum_score']:.2f}/100 (weight: 25%)")
    print(f"  Orbit stability score: {best_result['orbit_stability_score']:.2f}/100 (weight: 20%)")
    print(f"  Energy drift score: {best_result['energy_drift_score']:.2f}/100 (weight: 15%)")

    # Show top 10 configurations
    print(f"\nTop 10 configurations:")
    sorted_results = sorted(valid_results, key=lambda x: x['overall_score'], reverse=True)[:10]
    for i, r in enumerate(sorted_results, 1):
        print(f"  {i:2d}. Score={r['overall_score']:6.2f}, dt={r['dt']:4d}s, "
              f"soft={r['softening']:.0e}m, {r['integration_method']:6s}, "
              f"adaptive={str(r['adaptive_dt']):5s}")

    return best_result, results


def main():
    """Main entry point for enhanced hyperparameter optimization."""
    best_config, all_results = focused_hyperparameter_search()

    if best_config is None:
        print("\nOptimization failed!")
        return

    # Save required metrics output
    os.makedirs('.archivara/metrics', exist_ok=True)

    metrics_output = {
        "metric_name": "score",
        "value": best_config['overall_score'],
        "valid": True
    }

    with open('.archivara/metrics/a6b1a83a.json', 'w') as f:
        json.dump(metrics_output, f, indent=2)

    print(f"\n✓ Metrics saved to .archivara/metrics/a6b1a83a.json")

    # Save detailed results
    detailed_output = {
        'best_configuration': best_config,
        'all_results': all_results,
        'methodology': {
            'description': 'Enhanced hyperparameter optimization with extended metrics',
            'scoring_weights': {
                'energy_conservation': 0.40,
                'momentum_conservation': 0.25,
                'orbit_stability': 0.20,
                'energy_drift': 0.15
            },
            'improvements': [
                'Added orbit stability metric',
                'Added energy drift metric',
                'Tested adaptive timestep',
                'Expanded dt search space',
                'Refined softening parameters'
            ]
        }
    }

    with open('.archivara/metrics/a6b1a83a_detailed.json', 'w') as f:
        json.dump(detailed_output, f, indent=2)

    print(f"✓ Detailed results saved to .archivara/metrics/a6b1a83a_detailed.json")

    # Update optimal configuration
    config_code = f"""# Optimized hyperparameters for 3D Planetary Gravity Simulation
# Generated by enhanced hyperparameter optimization (v2)

OPTIMAL_CONFIG = {{
    # Core parameters
    'dt': {best_config['dt']},  # seconds ({best_config['dt']/3600:.2f} hours)
    'softening': {best_config['softening']},  # meters
    'integration_method': '{best_config['integration_method']}',
    'adaptive_dt': {best_config['adaptive_dt']},
    'num_steps': {best_config['num_steps']},

    # Performance metrics
    'overall_score': {best_config['overall_score']:.2f},
    'energy_error': {best_config['energy_error']:.6f},  # percent
    'momentum_error': {best_config['momentum_error']:.6f},  # percent
    'orbit_deviation': {best_config['orbit_deviation']:.4f},  # percent
    'energy_drift': {best_config['energy_drift']:.6f},  # percent

    # Component scores
    'energy_score': {best_config['energy_score']:.2f},
    'momentum_score': {best_config['momentum_score']:.2f},
    'orbit_stability_score': {best_config['orbit_stability_score']:.2f},
    'energy_drift_score': {best_config['energy_drift_score']:.2f},
}}

# Usage example:
# from optimal_config import OPTIMAL_CONFIG
# from hyperparameter_optimization import OptimizedGravitySimulation
# from main import create_solar_system_inner
#
# bodies = create_solar_system_inner()
# sim = OptimizedGravitySimulation(
#     bodies,
#     dt=OPTIMAL_CONFIG['dt'],
#     softening=OPTIMAL_CONFIG['softening'],
#     integration_method=OPTIMAL_CONFIG['integration_method']
# )
# sim.run(OPTIMAL_CONFIG['num_steps'])
"""

    with open('optimal_config.py', 'w') as f:
        f.write(config_code)

    print(f"✓ Updated configuration saved to optimal_config.py")

    print("\n" + "=" * 80)
    print("HYPERPARAMETER OPTIMIZATION COMPLETE")
    print("=" * 80)
    print(f"\nBest overall score: {best_config['overall_score']:.2f}/100")


if __name__ == "__main__":
    main()
