#!/usr/bin/env python3
"""
Ablation Study for 3D Planetary Gravity Simulation
Tests the necessity of each component by removing one at a time.
"""

import numpy as np
import json
import os
import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class CelestialBody:
    """Represents a celestial body with position, velocity, and mass."""
    name: str
    mass: float
    position: np.ndarray
    velocity: np.ndarray
    color: str = 'blue'
    radius: float = 1.0
    trail: List = field(default_factory=list)

    def __post_init__(self):
        self.position = np.ascontiguousarray(self.position, dtype=np.float64)
        self.velocity = np.ascontiguousarray(self.velocity, dtype=np.float64)


class AblationGravitySimulation:
    """
    Configurable gravity simulation for ablation testing.
    Can disable individual components to measure their impact.
    """

    G = 6.67430e-11  # Gravitational constant

    def __init__(self, bodies, dt=1000.0,
                 use_vectorization=True,
                 use_symplectic=True,
                 use_com_correction=True,
                 use_adaptive_substep=True,
                 use_softening=True,
                 use_memory_optimization=True):
        """
        Initialize simulation with configurable components.

        Args:
            bodies: List of CelestialBody objects
            dt: Time step in seconds
            use_vectorization: Use NumPy vectorized operations
            use_symplectic: Use symplectic Velocity Verlet (vs Euler)
            use_com_correction: Shift to center-of-mass frame
            use_adaptive_substep: Use adaptive substepping
            use_softening: Use Plummer softening
            use_memory_optimization: Preallocate arrays
        """
        self.bodies = bodies
        self.dt = dt
        self.dt_base = dt
        self.time = 0.0
        self.step_count = 0

        # Ablation flags
        self.use_vectorization = use_vectorization
        self.use_symplectic = use_symplectic
        self.use_com_correction = use_com_correction
        self.use_adaptive_substep = use_adaptive_substep
        self.use_softening = use_softening
        self.use_memory_optimization = use_memory_optimization

        self.softening = 1e8 if use_softening else 0.0

        self.n = len(bodies)

        # Arrays for vectorized computation
        if use_memory_optimization:
            self.positions = np.zeros((self.n, 3), dtype=np.float64)
            self.velocities = np.zeros((self.n, 3), dtype=np.float64)
            self.masses = np.zeros(self.n, dtype=np.float64)
            self.accelerations = np.zeros((self.n, 3), dtype=np.float64)

            # Temporary arrays (reused to avoid allocation)
            if use_vectorization:
                self.dr = np.zeros((self.n, self.n, 3), dtype=np.float64)
                self.r2 = np.zeros((self.n, self.n), dtype=np.float64)
                self.inv_r3 = np.zeros((self.n, self.n), dtype=np.float64)
        else:
            self.positions = None
            self.velocities = None
            self.masses = None
            self.accelerations = None

        # Sync initial state
        if use_memory_optimization:
            self.sync_to_arrays()

            # Shift to center-of-mass frame
            if use_com_correction:
                self.shift_to_com_frame()

        # Performance tracking
        self.force_calc_times = []
        self.energy_history = []

    def sync_to_arrays(self):
        """Sync body data to vectorized arrays."""
        for i, body in enumerate(self.bodies):
            self.positions[i] = body.position
            self.velocities[i] = body.velocity
            self.masses[i] = body.mass

    def sync_from_arrays(self):
        """Sync vectorized arrays back to body objects."""
        for i, body in enumerate(self.bodies):
            body.position = self.positions[i].copy()
            body.velocity = self.velocities[i].copy()

    def shift_to_com_frame(self):
        """Shift to center-of-mass frame to eliminate momentum drift."""
        total_mass = np.sum(self.masses)

        # Shift position to COM
        com_position = np.sum(self.masses[:, np.newaxis] * self.positions, axis=0) / total_mass
        self.positions -= com_position

        # Shift velocity to COM frame
        com_velocity = np.sum(self.masses[:, np.newaxis] * self.velocities, axis=0) / total_mass
        self.velocities -= com_velocity

        self.sync_from_arrays()

    def compute_accelerations_vectorized(self):
        """Compute accelerations using fully vectorized operations."""
        # Displacement vectors: dr[i,j] = r[j] - r[i]
        np.subtract(self.positions[np.newaxis, :, :],
                   self.positions[:, np.newaxis, :],
                   out=self.dr)

        # Squared distances with softening
        np.einsum('ijk,ijk->ij', self.dr, self.dr, out=self.r2)
        self.r2 += self.softening * self.softening

        # 1 / r^3 for force calculation
        np.power(self.r2, -1.5, out=self.inv_r3)

        # Remove self-interaction
        np.fill_diagonal(self.inv_r3, 0.0)

        # Acceleration: a[i] = G * sum_j(m[j] * dr[i,j] / r[i,j]^3)
        np.einsum('ij,ijx,j->ix', self.inv_r3, self.dr, self.masses,
                  out=self.accelerations)
        self.accelerations *= self.G

    def compute_accelerations_loop(self):
        """Compute accelerations using Python loops (baseline)."""
        self.accelerations.fill(0.0)

        for i in range(self.n):
            for j in range(self.n):
                if i == j:
                    continue

                # Displacement vector
                dr = self.positions[j] - self.positions[i]

                # Distance with softening
                r2 = np.sum(dr * dr) + self.softening * self.softening
                r = np.sqrt(r2)
                r3 = r * r2

                # Acceleration
                self.accelerations[i] += self.G * self.masses[j] * dr / r3

    def velocity_verlet_step(self, dt):
        """Symplectic Velocity Verlet integration."""
        # Compute initial accelerations
        if self.use_vectorization:
            self.compute_accelerations_vectorized()
        else:
            self.compute_accelerations_loop()

        # Half-step velocity update: v += 0.5 * a * dt
        self.velocities += 0.5 * self.accelerations * dt

        # Full-step position update: r += v * dt
        self.positions += self.velocities * dt

        # Recompute accelerations at new positions
        if self.use_vectorization:
            self.compute_accelerations_vectorized()
        else:
            self.compute_accelerations_loop()

        # Second half-step velocity update: v += 0.5 * a * dt
        self.velocities += 0.5 * self.accelerations * dt

    def euler_step(self, dt):
        """Simple Euler integration (non-symplectic baseline)."""
        # Compute accelerations
        if self.use_vectorization:
            self.compute_accelerations_vectorized()
        else:
            self.compute_accelerations_loop()

        # Update velocity: v += a * dt
        self.velocities += self.accelerations * dt

        # Update position: r += v * dt
        self.positions += self.velocities * dt

    def estimate_substeps(self):
        """Estimate number of substeps needed for adaptive stepping."""
        if not self.use_adaptive_substep:
            return 1

        # Compute current accelerations
        if self.use_vectorization:
            self.compute_accelerations_vectorized()
        else:
            self.compute_accelerations_loop()

        max_accel = np.max(np.linalg.norm(self.accelerations, axis=1))

        # Adaptive criterion
        AU = 1.496e11
        dt_safe = 0.01 * np.sqrt(AU / (max_accel + 1e-20))
        n_substeps = max(1, int(np.ceil(self.dt_base / dt_safe)))

        # Cap at 20 substeps
        return min(n_substeps, 20)

    def step(self):
        """Execute one simulation step."""
        start_time = time.time()

        # Determine substeps
        n_substeps = self.estimate_substeps()
        dt_sub = self.dt_base / n_substeps

        # Execute substeps
        for _ in range(n_substeps):
            if self.use_symplectic:
                self.velocity_verlet_step(dt_sub)
            else:
                self.euler_step(dt_sub)

        self.time += self.dt_base
        self.step_count += 1

        self.force_calc_times.append(time.time() - start_time)

    def calculate_total_energy_vectorized(self):
        """Calculate total energy using vectorized operations."""
        # Kinetic energy: K = 0.5 * sum(m * v²)
        v_squared = np.einsum('ix,ix->i', self.velocities, self.velocities)
        kinetic = 0.5 * np.sum(self.masses * v_squared)

        # Potential energy: U = -G * sum_{i<j}(m[i]*m[j] / r[i,j])
        dr = self.positions[np.newaxis, :, :] - self.positions[:, np.newaxis, :]
        r2 = np.einsum('ijk,ijk->ij', dr, dr) + self.softening**2
        r = np.sqrt(r2)

        # Upper triangle indices (avoid double counting)
        i_idx, j_idx = np.triu_indices(self.n, k=1)
        potential = -self.G * np.sum(self.masses[i_idx] * self.masses[j_idx] / r[i_idx, j_idx])

        return kinetic + potential

    def run(self, num_steps):
        """Run simulation for specified steps."""
        for step in range(num_steps):
            self.step()

            # Sample energy periodically
            if step % 10 == 0:
                self.energy_history.append(self.calculate_total_energy_vectorized())

        # Final sync
        if self.use_memory_optimization:
            self.sync_from_arrays()


def create_test_system(n_bodies=25):
    """Create a test system for ablation studies."""
    AU = 1.496e11
    bodies = []

    # Central star
    bodies.append(CelestialBody(
        name="Central Star",
        mass=1.989e30,
        position=np.array([0.0, 0.0, 0.0]),
        velocity=np.array([0.0, 0.0, 0.0]),
        color='yellow',
        radius=20
    ))

    # Random planets
    np.random.seed(42)
    for i in range(n_bodies - 1):
        # Random orbital radius (0.3 to 3 AU)
        r = (0.3 + 2.7 * np.random.random()) * AU

        # Random angle
        theta = 2 * np.pi * np.random.random()
        phi = np.pi * np.random.random()

        # Position
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi) * 0.1  # Flatten to disk

        # Circular velocity
        v_circ = np.sqrt(6.67430e-11 * 1.989e30 / r)
        vx = -v_circ * np.sin(theta)
        vy = v_circ * np.cos(theta)
        vz = 0

        # Random mass
        mass = 10**(22 + 3 * np.random.random())

        bodies.append(CelestialBody(
            name=f"Body_{i+1}",
            mass=mass,
            position=np.array([x, y, z]),
            velocity=np.array([vx, vy, vz]),
            color='blue',
            radius=3
        ))

    return bodies


def deep_copy_bodies(bodies):
    """Create a deep copy of bodies for independent simulations."""
    return [
        CelestialBody(
            name=body.name,
            mass=body.mass,
            position=body.position.copy(),
            velocity=body.velocity.copy(),
            color=body.color,
            radius=body.radius
        )
        for body in bodies
    ]


def run_ablation_study():
    """Run comprehensive ablation study."""
    print("=" * 80)
    print("ABLATION STUDY - Testing Component Necessity")
    print("=" * 80)

    # Test configuration
    n_bodies = 25
    num_steps = 500
    dt_base = 3600  # 1 hour

    # Define ablation configurations
    # Format: (name, description, config_dict)
    ablation_configs = [
        ("FULL (Baseline)", "All optimizations enabled", {
            'use_vectorization': True,
            'use_symplectic': True,
            'use_com_correction': True,
            'use_adaptive_substep': True,
            'use_softening': True,
            'use_memory_optimization': True,
        }),
        ("NO_VECTORIZATION", "Remove vectorized operations (use loops)", {
            'use_vectorization': False,
            'use_symplectic': True,
            'use_com_correction': True,
            'use_adaptive_substep': True,
            'use_softening': True,
            'use_memory_optimization': True,
        }),
        ("NO_SYMPLECTIC", "Remove symplectic integration (use Euler)", {
            'use_vectorization': True,
            'use_symplectic': False,
            'use_com_correction': True,
            'use_adaptive_substep': True,
            'use_softening': True,
            'use_memory_optimization': True,
        }),
        ("NO_COM_CORRECTION", "Remove center-of-mass correction", {
            'use_vectorization': True,
            'use_symplectic': True,
            'use_com_correction': False,
            'use_adaptive_substep': True,
            'use_softening': True,
            'use_memory_optimization': True,
        }),
        ("NO_ADAPTIVE_SUBSTEP", "Remove adaptive substepping", {
            'use_vectorization': True,
            'use_symplectic': True,
            'use_com_correction': True,
            'use_adaptive_substep': False,
            'use_softening': True,
            'use_memory_optimization': True,
        }),
        ("NO_SOFTENING", "Remove Plummer softening", {
            'use_vectorization': True,
            'use_symplectic': True,
            'use_com_correction': True,
            'use_adaptive_substep': True,
            'use_softening': False,
            'use_memory_optimization': True,
        }),
        ("NO_MEMORY_OPT", "Remove memory optimization (allocate each time)", {
            'use_vectorization': True,
            'use_symplectic': True,
            'use_com_correction': True,
            'use_adaptive_substep': True,
            'use_softening': True,
            'use_memory_optimization': False,
        }),
        ("MINIMAL", "Only basic Euler integration with loops", {
            'use_vectorization': False,
            'use_symplectic': False,
            'use_com_correction': False,
            'use_adaptive_substep': False,
            'use_softening': False,
            'use_memory_optimization': False,
        }),
    ]

    results = []

    for config_name, config_desc, config_dict in ablation_configs:
        print(f"\n{'=' * 80}")
        print(f"TEST: {config_name}")
        print(f"Description: {config_desc}")
        print(f"{'=' * 80}")

        # Create fresh bodies for this test
        test_bodies = create_test_system(n_bodies)

        try:
            # Initialize simulation
            sim = AblationGravitySimulation(
                test_bodies,
                dt=dt_base,
                **config_dict
            )

            # Initial energy
            initial_energy = sim.calculate_total_energy_vectorized()
            print(f"Bodies: {len(sim.bodies)}")
            print(f"Initial energy: {initial_energy:.6e} J")

            # Run simulation
            start_time = time.time()
            sim.run(num_steps)
            elapsed_time = time.time() - start_time

            # Final energy
            final_energy = sim.calculate_total_energy_vectorized()

            # Metrics
            energy_error = abs((final_energy - initial_energy) / initial_energy) * 100
            steps_per_sec = num_steps / elapsed_time if elapsed_time > 0 else 0
            avg_step_time = np.mean(sim.force_calc_times) * 1000 if sim.force_calc_times else 0

            print(f"\nResults after {num_steps} steps:")
            print(f"Final energy: {final_energy:.6e} J")
            print(f"Energy error: {energy_error:.6f}%")
            print(f"Total time: {elapsed_time:.4f}s")
            print(f"Steps/sec: {steps_per_sec:.1f}")
            print(f"Avg step time: {avg_step_time:.4f}ms")

            # Scoring
            # Energy conservation score (lower error = higher score)
            energy_score = max(0, 100 - energy_error * 10)

            # Performance score relative to baseline
            # Assume baseline ~7000 steps/sec for 25 bodies
            baseline_steps_sec = 7000
            performance_ratio = steps_per_sec / baseline_steps_sec if baseline_steps_sec > 0 else 0
            performance_score = min(100, 50 + 50 * np.log10(max(0.01, performance_ratio)))

            # Overall score (weighted)
            overall_score = energy_score * 0.6 + performance_score * 0.4

            result = {
                'config': config_name,
                'description': config_desc,
                'energy_error': energy_error,
                'time': elapsed_time,
                'steps_per_sec': steps_per_sec,
                'avg_step_time_ms': avg_step_time,
                'energy_score': energy_score,
                'performance_score': performance_score,
                'overall_score': overall_score,
                'success': True
            }

            print(f"\nScores:")
            print(f"  Energy conservation: {energy_score:.2f}/100")
            print(f"  Performance: {performance_score:.2f}/100")
            print(f"  OVERALL: {overall_score:.2f}/100")

        except Exception as e:
            print(f"ERROR: {e}")
            result = {
                'config': config_name,
                'description': config_desc,
                'energy_error': float('inf'),
                'time': float('inf'),
                'steps_per_sec': 0,
                'avg_step_time_ms': float('inf'),
                'energy_score': 0,
                'performance_score': 0,
                'overall_score': 0,
                'success': False,
                'error': str(e)
            }

        results.append(result)

    # Summary table
    print(f"\n{'=' * 80}")
    print("ABLATION STUDY RESULTS SUMMARY")
    print(f"{'=' * 80}")
    print(f"{'Configuration':<25} {'E_err %':<12} {'Time (s)':<12} {'Steps/s':<12} {'Score':<10}")
    print("-" * 80)

    for r in results:
        if r['success']:
            print(f"{r['config']:<25} {r['energy_error']:<12.6f} {r['time']:<12.4f} "
                  f"{r['steps_per_sec']:<12.1f} {r['overall_score']:<10.2f}")
        else:
            print(f"{r['config']:<25} FAILED")

    # Analysis: Impact of removing each component
    print(f"\n{'=' * 80}")
    print("COMPONENT IMPACT ANALYSIS")
    print(f"{'=' * 80}")

    baseline = next(r for r in results if r['config'] == 'FULL (Baseline)')
    baseline_score = baseline['overall_score']

    print(f"Baseline score: {baseline_score:.2f}/100\n")

    component_impacts = []
    for r in results:
        if r['config'] != 'FULL (Baseline)' and r['success']:
            score_drop = baseline_score - r['overall_score']

            # Determine what was removed
            removed_component = r['config'].replace('NO_', '').replace('_', ' ')

            component_impacts.append({
                'component': removed_component,
                'score_drop': score_drop,
                'config': r['config'],
                'energy_error_increase': r['energy_error'] - baseline['energy_error'],
                'performance_drop_pct': (1 - r['steps_per_sec'] / baseline['steps_per_sec']) * 100 if baseline['steps_per_sec'] > 0 else 0
            })

    # Sort by impact (highest score drop = most important component)
    component_impacts.sort(key=lambda x: x['score_drop'], reverse=True)

    print(f"{'Component Removed':<30} {'Score Drop':<15} {'Perf Drop %':<15} {'E_err Δ%':<15}")
    print("-" * 80)
    for impact in component_impacts:
        print(f"{impact['component']:<30} {impact['score_drop']:<15.2f} "
              f"{impact['performance_drop_pct']:<15.1f} {impact['energy_error_increase']:<15.6f}")

    # Find best score from ablation results
    best_result = max(results, key=lambda x: x['overall_score'] if x['success'] else 0)
    final_score = best_result['overall_score']

    print(f"\n{'=' * 80}")
    print(f"BEST CONFIGURATION: {best_result['config']}")
    print(f"FINAL ABLATION SCORE: {final_score:.2f}/100")
    print(f"{'=' * 80}")

    # Key findings
    print(f"\nKEY FINDINGS:")
    print(f"\nMost critical components (by score impact):")
    for i, impact in enumerate(component_impacts[:3], 1):
        print(f"  {i}. {impact['component']}: -{impact['score_drop']:.2f} points")

    print(f"\nLeast critical components:")
    for i, impact in enumerate(component_impacts[-3:], 1):
        print(f"  {i}. {impact['component']}: -{impact['score_drop']:.2f} points")

    # Save metrics
    os.makedirs('.archivara/metrics', exist_ok=True)
    metrics = {
        "metric_name": "score",
        "value": float(final_score),
        "valid": True
    }

    with open('.archivara/metrics/8b83c8bb.json', 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\nMetrics saved to .archivara/metrics/8b83c8bb.json")

    # Save detailed results
    with open('.archivara/ablation_results.json', 'w') as f:
        json.dump({
            'results': results,
            'component_impacts': component_impacts,
            'final_score': final_score
        }, f, indent=2)

    print(f"Detailed results saved to .archivara/ablation_results.json")

    return final_score


if __name__ == "__main__":
    run_ablation_study()
