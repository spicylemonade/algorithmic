#!/usr/bin/env python3
"""
Hyperparameter Optimization for 3D Planetary Gravity Simulation
Tunes simulation parameters for optimal accuracy and stability
"""

import numpy as np
import json
import os
from itertools import product
from main import GravitySimulation, create_solar_system_inner, CelestialBody


class OptimizedGravitySimulation(GravitySimulation):
    """Extended simulation with configurable hyperparameters."""

    def __init__(self, bodies, dt=1000.0, softening=0.0, integration_method='verlet'):
        """
        Initialize simulation with hyperparameters.

        Args:
            bodies: List of CelestialBody objects
            dt: Time step in seconds
            softening: Softening parameter to prevent singularities (meters)
            integration_method: Integration method ('verlet', 'euler', 'rk4')
        """
        super().__init__(bodies, dt)
        self.softening = softening
        self.integration_method = integration_method

    def calculate_forces_softened(self):
        """Calculate gravitational forces with softening parameter."""
        for body in self.bodies:
            body.acceleration = np.zeros(3, dtype=np.float64)

        for i, body1 in enumerate(self.bodies):
            for j, body2 in enumerate(self.bodies):
                if i >= j:
                    continue

                r_vec = body2.position - body1.position
                r_mag = np.linalg.norm(r_vec)

                # Apply softening: r_eff = sqrt(r^2 + epsilon^2)
                r_eff = np.sqrt(r_mag**2 + self.softening**2)

                if r_eff < 1e-10:
                    continue

                # F = G * m1 * m2 / r_eff^2
                force_mag = self.G * body1.mass * body2.mass / (r_eff ** 2)
                force_dir = r_vec / r_mag if r_mag > 1e-10 else np.zeros(3)

                body1.acceleration += force_mag * force_dir / body1.mass
                body2.acceleration -= force_mag * force_dir / body2.mass

    def step_euler(self):
        """Simple Euler integration (less accurate but faster)."""
        if self.softening > 0:
            self.calculate_forces_softened()
        else:
            self.calculate_forces()

        for body in self.bodies:
            body.velocity += body.acceleration * self.dt
            body.position += body.velocity * self.dt

            if len(body.trail) < 500:
                body.trail.append(body.position.copy())
            else:
                body.trail.pop(0)
                body.trail.append(body.position.copy())

        self.time += self.dt

    def step_rk4(self):
        """4th order Runge-Kutta integration (more accurate but slower)."""
        def derivatives(positions, velocities):
            """Calculate accelerations for given positions."""
            old_positions = [body.position.copy() for body in self.bodies]
            old_velocities = [body.velocity.copy() for body in self.bodies]

            for i, body in enumerate(self.bodies):
                body.position = positions[i].copy()
                body.velocity = velocities[i].copy()

            if self.softening > 0:
                self.calculate_forces_softened()
            else:
                self.calculate_forces()

            accs = [body.acceleration.copy() for body in self.bodies]

            for i, body in enumerate(self.bodies):
                body.position = old_positions[i]
                body.velocity = old_velocities[i]

            return accs

        positions = [body.position.copy() for body in self.bodies]
        velocities = [body.velocity.copy() for body in self.bodies]

        # RK4 steps
        k1v = derivatives(positions, velocities)
        k1x = velocities

        pos2 = [positions[i] + 0.5 * self.dt * k1x[i] for i in range(len(self.bodies))]
        vel2 = [velocities[i] + 0.5 * self.dt * k1v[i] for i in range(len(self.bodies))]
        k2v = derivatives(pos2, vel2)
        k2x = vel2

        pos3 = [positions[i] + 0.5 * self.dt * k2x[i] for i in range(len(self.bodies))]
        vel3 = [velocities[i] + 0.5 * self.dt * k2v[i] for i in range(len(self.bodies))]
        k3v = derivatives(pos3, vel3)
        k3x = vel3

        pos4 = [positions[i] + self.dt * k3x[i] for i in range(len(self.bodies))]
        vel4 = [velocities[i] + self.dt * k3v[i] for i in range(len(self.bodies))]
        k4v = derivatives(pos4, vel4)
        k4x = vel4

        # Update positions and velocities
        for i, body in enumerate(self.bodies):
            body.position += (self.dt / 6.0) * (k1x[i] + 2*k2x[i] + 2*k3x[i] + k4x[i])
            body.velocity += (self.dt / 6.0) * (k1v[i] + 2*k2v[i] + 2*k3v[i] + k4v[i])

            if len(body.trail) < 500:
                body.trail.append(body.position.copy())
            else:
                body.trail.pop(0)
                body.trail.append(body.position.copy())

        self.time += self.dt

    def step_verlet_softened(self):
        """Velocity Verlet with softening."""
        if self.softening > 0:
            self.calculate_forces_softened()
        else:
            self.calculate_forces()

        old_accelerations = [body.acceleration.copy() for body in self.bodies]

        for body in self.bodies:
            body.position += body.velocity * self.dt + 0.5 * body.acceleration * self.dt ** 2

        if self.softening > 0:
            self.calculate_forces_softened()
        else:
            self.calculate_forces()

        for i, body in enumerate(self.bodies):
            body.velocity += 0.5 * (old_accelerations[i] + body.acceleration) * self.dt

            if len(body.trail) < 500:
                body.trail.append(body.position.copy())
            else:
                body.trail.pop(0)
                body.trail.append(body.position.copy())

        self.time += self.dt

    def step(self):
        """Execute one simulation step using configured method."""
        if self.integration_method == 'euler':
            self.step_euler()
        elif self.integration_method == 'rk4':
            self.step_rk4()
        else:  # verlet
            self.step_verlet_softened()

    def run(self, num_steps):
        """Run simulation for a number of steps."""
        for _ in range(num_steps):
            self.step()
            self.energy_history.append(self.calculate_total_energy())


def evaluate_hyperparameters(dt, softening, integration_method, num_steps=1000):
    """
    Evaluate a hyperparameter configuration.

    Returns:
        dict: Metrics including energy conservation, momentum conservation, and score
    """
    # Create fresh solar system
    bodies = create_solar_system_inner()

    # Initialize simulation
    sim = OptimizedGravitySimulation(
        bodies,
        dt=dt,
        softening=softening,
        integration_method=integration_method
    )

    # Calculate initial values
    initial_energy = sim.calculate_total_energy()
    initial_momentum = sim.calculate_momentum()

    # Run simulation
    sim.run(num_steps)

    # Calculate final values
    final_energy = sim.calculate_total_energy()
    final_momentum = sim.calculate_momentum()

    # Conservation metrics
    energy_error = abs((final_energy - initial_energy) / initial_energy) * 100
    momentum_error = abs((final_momentum - initial_momentum) / max(initial_momentum, 1e-10)) * 100

    # Check for numerical stability (NaN or Inf)
    is_valid = not (np.isnan(final_energy) or np.isinf(final_energy) or
                   np.isnan(final_momentum) or np.isinf(final_momentum))

    # Calculate scores
    energy_score = max(0, 100 - energy_error * 10) if is_valid else 0
    momentum_score = max(0, 100 - momentum_error * 10) if is_valid else 0
    stability_score = 100 if is_valid and len(sim.bodies) == len(bodies) else 0

    overall_score = (energy_score + momentum_score + stability_score) / 3

    return {
        'dt': dt,
        'softening': softening,
        'integration_method': integration_method,
        'num_steps': num_steps,
        'energy_error': energy_error if is_valid else float('inf'),
        'momentum_error': momentum_error if is_valid else float('inf'),
        'energy_score': energy_score,
        'momentum_score': momentum_score,
        'stability_score': stability_score,
        'overall_score': overall_score,
        'is_valid': is_valid,
        'simulation_time_days': num_steps * dt / (24 * 3600)
    }


def hyperparameter_search():
    """
    Perform grid search over hyperparameter space.
    """
    print("=" * 70)
    print("HYPERPARAMETER OPTIMIZATION FOR 3D PLANETARY GRAVITY SIMULATION")
    print("=" * 70)

    # Define search space
    dt_values = [1800, 3600, 7200, 14400]  # 0.5h, 1h, 2h, 4h
    softening_values = [0.0, 1e8, 1e9, 1e10]  # No softening to significant softening
    integration_methods = ['verlet', 'euler', 'rk4']
    num_steps = 1000  # Fixed for all experiments

    print(f"\nSearch space:")
    print(f"  dt: {dt_values} (time steps in seconds)")
    print(f"  softening: {softening_values} (meters)")
    print(f"  integration_method: {integration_methods}")
    print(f"  num_steps: {num_steps} (fixed)")
    print(f"\nTotal configurations: {len(dt_values) * len(softening_values) * len(integration_methods)}")

    # Run grid search
    results = []
    total_configs = len(dt_values) * len(softening_values) * len(integration_methods)
    current = 0

    print("\n" + "=" * 70)
    print("Running experiments...")
    print("=" * 70)

    for dt in dt_values:
        for softening in softening_values:
            for method in integration_methods:
                current += 1
                print(f"\n[{current}/{total_configs}] Testing: dt={dt}s, softening={softening:.0e}m, method={method}")

                try:
                    result = evaluate_hyperparameters(dt, softening, method, num_steps)
                    results.append(result)

                    print(f"  Energy error: {result['energy_error']:.4f}%")
                    print(f"  Momentum error: {result['momentum_error']:.4f}%")
                    print(f"  Overall score: {result['overall_score']:.2f}/100")
                    print(f"  Valid: {result['is_valid']}")

                except Exception as e:
                    print(f"  ERROR: {e}")
                    results.append({
                        'dt': dt,
                        'softening': softening,
                        'integration_method': method,
                        'overall_score': 0.0,
                        'is_valid': False,
                        'error': str(e)
                    })

    # Find best configuration
    valid_results = [r for r in results if r.get('is_valid', False)]

    if not valid_results:
        print("\nERROR: No valid configurations found!")
        return None, results

    best_result = max(valid_results, key=lambda x: x['overall_score'])

    print("\n" + "=" * 70)
    print("OPTIMIZATION RESULTS")
    print("=" * 70)

    print(f"\nBest configuration:")
    print(f"  Time step (dt): {best_result['dt']} seconds ({best_result['dt']/3600:.2f} hours)")
    print(f"  Softening: {best_result['softening']:.2e} meters")
    print(f"  Integration method: {best_result['integration_method']}")
    print(f"\nPerformance:")
    print(f"  Overall score: {best_result['overall_score']:.2f}/100")
    print(f"  Energy conservation error: {best_result['energy_error']:.4f}%")
    print(f"  Momentum conservation error: {best_result['momentum_error']:.4f}%")
    print(f"  Simulation duration: {best_result['simulation_time_days']:.1f} days")

    # Show top 5 configurations
    print(f"\nTop 5 configurations:")
    sorted_results = sorted(valid_results, key=lambda x: x['overall_score'], reverse=True)[:5]
    for i, r in enumerate(sorted_results, 1):
        print(f"  {i}. Score={r['overall_score']:.2f}, dt={r['dt']}s, "
              f"soft={r['softening']:.0e}m, method={r['integration_method']}")

    return best_result, results


def main():
    """Main entry point for hyperparameter optimization."""
    # Run hyperparameter search
    best_config, all_results = hyperparameter_search()

    if best_config is None:
        print("\nOptimization failed!")
        return

    # Save results
    os.makedirs('.archivara/metrics', exist_ok=True)

    # Save best configuration metrics (required format)
    metrics_output = {
        "metric_name": "score",
        "value": best_config['overall_score'],
        "valid": True
    }

    with open('.archivara/metrics/a4f875da.json', 'w') as f:
        json.dump(metrics_output, f, indent=2)

    print(f"\n✓ Metrics saved to .archivara/metrics/a4f875da.json")

    # Save detailed results
    detailed_output = {
        'best_configuration': best_config,
        'all_results': all_results,
        'search_space': {
            'dt_values': [1800, 3600, 7200, 14400],
            'softening_values': [0.0, 1e8, 1e9, 1e10],
            'integration_methods': ['verlet', 'euler', 'rk4']
        }
    }

    with open('.archivara/metrics/a4f875da_detailed.json', 'w') as f:
        json.dump(detailed_output, f, indent=2)

    print(f"✓ Detailed results saved to .archivara/metrics/a4f875da_detailed.json")

    # Save best configuration as Python config
    config_code = f"""# Optimized hyperparameters for 3D Planetary Gravity Simulation
# Generated by hyperparameter optimization

OPTIMAL_CONFIG = {{
    'dt': {best_config['dt']},  # Time step in seconds ({best_config['dt']/3600:.2f} hours)
    'softening': {best_config['softening']},  # Softening parameter in meters
    'integration_method': '{best_config['integration_method']}',  # Integration method
    'num_steps': {best_config['num_steps']},  # Number of steps

    # Performance metrics
    'overall_score': {best_config['overall_score']:.2f},
    'energy_error': {best_config['energy_error']:.4f},  # percent
    'momentum_error': {best_config['momentum_error']:.4f},  # percent
}}
"""

    with open('optimal_config.py', 'w') as f:
        f.write(config_code)

    print(f"✓ Configuration saved to optimal_config.py")

    print("\n" + "=" * 70)
    print("HYPERPARAMETER OPTIMIZATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
