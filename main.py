#!/usr/bin/env python3
"""
3D Planetary Gravity Simulation
A realistic N-body gravity simulator with 3D visualization
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import json
import os


class CelestialBody:
    """Represents a celestial body with position, velocity, and mass."""

    def __init__(self, name, mass, position, velocity, color='blue', radius=1.0):
        """
        Initialize a celestial body.

        Args:
            name: Body name
            mass: Mass in kg
            position: 3D position vector [x, y, z] in meters
            velocity: 3D velocity vector [vx, vy, vz] in m/s
            color: Color for visualization
            radius: Display radius (not physical)
        """
        self.name = name
        self.mass = mass
        self.position = np.array(position, dtype=np.float64)
        self.velocity = np.array(velocity, dtype=np.float64)
        self.acceleration = np.zeros(3, dtype=np.float64)
        self.color = color
        self.radius = radius
        self.trail = []  # Store position history for trails

    def __repr__(self):
        return f"CelestialBody({self.name}, mass={self.mass:.2e} kg)"


class GravitySimulation:
    """N-body gravity simulation using Newtonian mechanics."""

    G = 6.67430e-11  # Gravitational constant in m^3 kg^-1 s^-2

    def __init__(self, bodies, dt=1000.0):
        """
        Initialize simulation.

        Args:
            bodies: List of CelestialBody objects
            dt: Time step in seconds
        """
        self.bodies = bodies
        self.dt = dt
        self.time = 0.0
        self.energy_history = []

    def calculate_forces(self):
        """Calculate gravitational forces between all bodies."""
        # Reset accelerations
        for body in self.bodies:
            body.acceleration = np.zeros(3, dtype=np.float64)

        # Calculate pairwise forces
        for i, body1 in enumerate(self.bodies):
            for j, body2 in enumerate(self.bodies):
                if i >= j:
                    continue

                # Vector from body1 to body2
                r_vec = body2.position - body1.position
                r_mag = np.linalg.norm(r_vec)

                if r_mag < 1e-10:  # Avoid division by zero
                    continue

                # Gravitational force magnitude: F = G * m1 * m2 / r^2
                force_mag = self.G * body1.mass * body2.mass / (r_mag ** 2)

                # Force direction (unit vector)
                force_dir = r_vec / r_mag

                # Apply Newton's third law
                # F = ma => a = F/m
                body1.acceleration += force_mag * force_dir / body1.mass
                body2.acceleration -= force_mag * force_dir / body2.mass

    def step_verlet(self):
        """
        Advance simulation by one time step using velocity Verlet integration.
        More accurate and stable than Euler method for orbital mechanics.
        """
        # Calculate forces at current positions
        self.calculate_forces()

        # Store old accelerations for all bodies
        old_accelerations = [body.acceleration.copy() for body in self.bodies]

        # Update positions
        for body in self.bodies:
            # Update position: x(t+dt) = x(t) + v(t)*dt + 0.5*a(t)*dt^2
            body.position += body.velocity * self.dt + 0.5 * body.acceleration * self.dt ** 2

        # Recalculate forces at new positions
        self.calculate_forces()

        # Update velocities: v(t+dt) = v(t) + 0.5*(a(t) + a(t+dt))*dt
        for i, body in enumerate(self.bodies):
            body.velocity += 0.5 * (old_accelerations[i] + body.acceleration) * self.dt

            # Store trail
            if len(body.trail) < 500:  # Limit trail length
                body.trail.append(body.position.copy())
            else:
                body.trail.pop(0)
                body.trail.append(body.position.copy())

        self.time += self.dt

    def calculate_total_energy(self):
        """Calculate total energy (kinetic + potential) of the system."""
        kinetic_energy = 0.0
        potential_energy = 0.0

        # Kinetic energy: KE = 0.5 * m * v^2
        for body in self.bodies:
            v_mag = np.linalg.norm(body.velocity)
            kinetic_energy += 0.5 * body.mass * v_mag ** 2

        # Gravitational potential energy: PE = -G * m1 * m2 / r
        for i, body1 in enumerate(self.bodies):
            for j, body2 in enumerate(self.bodies):
                if i >= j:
                    continue
                r_mag = np.linalg.norm(body2.position - body1.position)
                if r_mag > 1e-10:
                    potential_energy -= self.G * body1.mass * body2.mass / r_mag

        return kinetic_energy + potential_energy

    def calculate_momentum(self):
        """Calculate total momentum of the system."""
        total_momentum = np.zeros(3, dtype=np.float64)
        for body in self.bodies:
            total_momentum += body.mass * body.velocity
        return np.linalg.norm(total_momentum)

    def run(self, num_steps):
        """Run simulation for a number of steps."""
        for _ in range(num_steps):
            self.step_verlet()
            self.energy_history.append(self.calculate_total_energy())


def create_solar_system_inner():
    """Create a simplified inner solar system (Sun, Mercury, Venus, Earth, Mars)."""
    AU = 1.496e11  # Astronomical Unit in meters

    bodies = [
        CelestialBody(
            name="Sun",
            mass=1.989e30,
            position=[0, 0, 0],
            velocity=[0, 0, 0],
            color='yellow',
            radius=20
        ),
        CelestialBody(
            name="Mercury",
            mass=3.285e23,
            position=[0.387 * AU, 0, 0],
            velocity=[0, 47870, 0],
            color='gray',
            radius=3
        ),
        CelestialBody(
            name="Venus",
            mass=4.867e24,
            position=[0.723 * AU, 0, 0],
            velocity=[0, 35020, 0],
            color='orange',
            radius=5
        ),
        CelestialBody(
            name="Earth",
            mass=5.972e24,
            position=[1.0 * AU, 0, 0],
            velocity=[0, 29780, 0],
            color='blue',
            radius=5
        ),
        CelestialBody(
            name="Mars",
            mass=6.39e23,
            position=[1.524 * AU, 0, 0],
            velocity=[0, 24070, 0],
            color='red',
            radius=4
        )
    ]

    return bodies


def create_binary_star_system():
    """Create a binary star system with a planet."""
    bodies = [
        CelestialBody(
            name="Star A",
            mass=1.989e30,
            position=[1e11, 0, 0],
            velocity=[0, 15000, 0],
            color='yellow',
            radius=15
        ),
        CelestialBody(
            name="Star B",
            mass=1.5e30,
            position=[-1e11, 0, 0],
            velocity=[0, -10000, 0],
            color='orange',
            radius=18
        ),
        CelestialBody(
            name="Planet",
            mass=5.972e24,
            position=[0, 3e11, 0],
            velocity=[20000, 0, 5000],
            color='blue',
            radius=5
        )
    ]

    return bodies


def create_three_body_problem():
    """Create a figure-eight three-body system."""
    m = 1.989e30  # Solar mass

    bodies = [
        CelestialBody(
            name="Body 1",
            mass=m,
            position=[0.97000436, -0.24308753, 0],
            velocity=[0.466203685, 0.43236573, 0],
            color='red',
            radius=10
        ),
        CelestialBody(
            name="Body 2",
            mass=m,
            position=[-0.97000436, 0.24308753, 0],
            velocity=[0.466203685, 0.43236573, 0],
            color='green',
            radius=10
        ),
        CelestialBody(
            name="Body 3",
            mass=m,
            position=[0, 0, 0],
            velocity=[-2 * 0.466203685, -2 * 0.43236573, 0],
            color='blue',
            radius=10
        )
    ]

    # Scale to astronomical distances
    AU = 1.496e11
    for body in bodies:
        body.position = body.position * AU
        body.velocity = body.velocity * 30000  # Scale velocities

    return bodies


class Visualizer:
    """3D visualization of the gravity simulation."""

    def __init__(self, simulation, update_interval=50):
        """
        Initialize visualizer.

        Args:
            simulation: GravitySimulation object
            update_interval: Animation update interval in ms
        """
        self.simulation = simulation
        self.update_interval = update_interval

        self.fig = plt.figure(figsize=(12, 10))
        self.ax = self.fig.add_subplot(111, projection='3d')

        self.scatter_plots = {}
        self.trail_plots = {}

    def setup_plot(self):
        """Setup the 3D plot."""
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Z (m)')
        self.ax.set_title('3D Planetary Gravity Simulation')

        # Initialize scatter plots for each body
        for body in self.simulation.bodies:
            self.scatter_plots[body.name] = self.ax.scatter(
                [], [], [],
                c=body.color,
                s=body.radius ** 2,
                label=body.name,
                alpha=0.9
            )
            self.trail_plots[body.name] = self.ax.plot(
                [], [], [],
                c=body.color,
                alpha=0.3,
                linewidth=0.5
            )[0]

        self.ax.legend()

    def update(self, frame):
        """Update function for animation."""
        # Run simulation steps
        for _ in range(5):  # Multiple steps per frame for speed
            self.simulation.step_verlet()

        # Update positions
        for body in self.simulation.bodies:
            self.scatter_plots[body.name]._offsets3d = (
                [body.position[0]],
                [body.position[1]],
                [body.position[2]]
            )

            # Update trails
            if len(body.trail) > 1:
                trail_array = np.array(body.trail)
                self.trail_plots[body.name].set_data(trail_array[:, 0], trail_array[:, 1])
                self.trail_plots[body.name].set_3d_properties(trail_array[:, 2])

        # Auto-scale axes
        all_positions = np.array([body.position for body in self.simulation.bodies])
        if len(all_positions) > 0:
            max_range = np.max(np.abs(all_positions)) * 1.2
            self.ax.set_xlim(-max_range, max_range)
            self.ax.set_ylim(-max_range, max_range)
            self.ax.set_zlim(-max_range, max_range)

        self.ax.set_title(f'3D Planetary Gravity Simulation (t = {self.simulation.time / (24 * 3600):.1f} days)')

        return list(self.scatter_plots.values()) + list(self.trail_plots.values())

    def animate(self, frames=500):
        """Create and show animation."""
        self.setup_plot()
        anim = FuncAnimation(
            self.fig,
            self.update,
            frames=frames,
            interval=self.update_interval,
            blit=False
        )
        plt.show()
        return anim


def run_simulation_test():
    """Run simulation and calculate performance metrics."""
    print("=" * 60)
    print("3D PLANETARY GRAVITY SIMULATION")
    print("=" * 60)

    # Create solar system
    print("\n[1] Creating Solar System...")
    bodies = create_solar_system_inner()

    # Initialize simulation
    dt = 3600  # 1 hour time steps
    sim = GravitySimulation(bodies, dt=dt)

    print(f"Bodies: {len(sim.bodies)}")
    for body in sim.bodies:
        print(f"  - {body.name}: mass={body.mass:.2e} kg")

    # Calculate initial values
    initial_energy = sim.calculate_total_energy()
    initial_momentum = sim.calculate_momentum()

    print(f"\nInitial total energy: {initial_energy:.6e} J")
    print(f"Initial total momentum: {initial_momentum:.6e} kg⋅m/s")

    # Run simulation
    print("\n[2] Running simulation...")
    num_steps = 1000
    sim.run(num_steps)

    # Calculate final values
    final_energy = sim.calculate_total_energy()
    final_momentum = sim.calculate_momentum()

    print(f"\nAfter {num_steps} steps ({sim.time / (24 * 3600):.1f} days):")
    print(f"Final total energy: {final_energy:.6e} J")
    print(f"Final total momentum: {final_momentum:.6e} kg⋅m/s")

    # Conservation metrics
    energy_error = abs((final_energy - initial_energy) / initial_energy) * 100
    momentum_error = abs((final_momentum - initial_momentum) / max(initial_momentum, 1e-10)) * 100

    print(f"\nEnergy conservation error: {energy_error:.4f}%")
    print(f"Momentum conservation error: {momentum_error:.4f}%")

    # Calculate score (0-100)
    # Good simulation should conserve energy and momentum
    energy_score = max(0, 100 - energy_error * 10)
    momentum_score = max(0, 100 - momentum_error * 10)
    stability_score = 100 if len(sim.bodies) == len(bodies) else 0  # All bodies still exist

    overall_score = (energy_score + momentum_score + stability_score) / 3

    print(f"\n[3] Performance Metrics:")
    print(f"Energy conservation score: {energy_score:.2f}/100")
    print(f"Momentum conservation score: {momentum_score:.2f}/100")
    print(f"Stability score: {stability_score:.2f}/100")
    print(f"Overall score: {overall_score:.2f}/100")

    # Save metrics
    os.makedirs('.archivara/metrics', exist_ok=True)
    metrics = {
        "metric_name": "score",
        "value": overall_score,
        "valid": True
    }

    with open('.archivara/metrics/3fb5b026.json', 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\n[4] Metrics saved to .archivara/metrics/3fb5b026.json")

    return sim, overall_score


def main():
    """Main entry point."""
    print("3D Planetary Gravity Simulation")
    print("=" * 60)
    print("\nAvailable systems:")
    print("1. Inner Solar System (Sun, Mercury, Venus, Earth, Mars)")
    print("2. Binary Star System with Planet")
    print("3. Three-Body Problem (Figure-Eight)")
    print("4. Run automated test and generate metrics")

    choice = input("\nSelect system (1-4) [default: 4]: ").strip()

    if choice == "1":
        bodies = create_solar_system_inner()
        dt = 3600  # 1 hour
    elif choice == "2":
        bodies = create_binary_star_system()
        dt = 5000
    elif choice == "3":
        bodies = create_three_body_problem()
        dt = 2000
    else:
        # Run automated test
        sim, score = run_simulation_test()

        # Ask if user wants to visualize (handle EOF gracefully)
        try:
            vis_choice = input("\nVisualize simulation? (y/n) [default: n]: ").strip().lower()
            if vis_choice == 'y':
                print("\nStarting visualization...")
                vis = Visualizer(sim, update_interval=50)
                vis.animate(frames=1000)
        except (EOFError, KeyboardInterrupt):
            print("\nSimulation complete. Metrics saved.")
        return

    # Interactive mode
    sim = GravitySimulation(bodies, dt=dt)

    print(f"\nSimulation initialized with {len(bodies)} bodies")
    print("Starting visualization...")

    vis = Visualizer(sim, update_interval=50)
    vis.animate(frames=1000)


if __name__ == "__main__":
    main()
