import numpy as np
from typing import List
from .base import BaseEngine, SimulationParams, SimulationState
from pydantic import Field

class PhysicsParams(SimulationParams):
    """Universe dials for Newtonian physics."""
    G: float = Field(6.67430e-11, description="Gravitational constant - tune for different regimes")
    num_particles: int = Field(50, gt=0, le=500)
    softening: float = 0.1  # Prevent singularities
    mass: float = 1.0

class PhysicsEngine(BaseEngine):
    """N-body gravity simulation. First production engine.
    
    Trade-offs: NumPy vectorized for speed vs. pure Python readability.
    Edge case: High particle count - O(n^2) -> future GPU/approx.
    Assumption: 2D for viz simplicity (extendable to 3D).
    """
    def __init__(self):
        super().__init__()
        self.name = "physics"

    def initialize(self, params: PhysicsParams) -> SimulationState:
        """Random initial conditions in unit box."""
        np.random.seed(42)  # Reproducibility - key for hypothesis testing
        positions = np.random.rand(params.num_particles, 2) * 10 - 5
        velocities = np.random.randn(params.num_particles, 2) * 0.1
        return SimulationState(
            positions=positions.tolist(),
            velocities=velocities.tolist(),
            metadata={"params": params.model_dump(), "step": 0}
        )

    def step(self, state: SimulationState, params: PhysicsParams) -> SimulationState:
        """Euler integration with softened gravity."""
        pos = np.array(state.positions)
        vel = np.array(state.velocities)
        n = len(pos)

        # Compute forces
        forces = np.zeros_like(pos)
        for i in range(n):
            for j in range(i+1, n):
                r = pos[j] - pos[i]
                dist = np.linalg.norm(r)
                if dist > 1e-6:
                    f = params.G * params.mass**2 / (dist**2 + params.softening**2)
                    dir_unit = r / dist
                    forces[i] += f * dir_unit
                    forces[j] -= f * dir_unit

        # Update velocities and positions
        vel += (forces / params.mass) * params.dt
        pos += vel * params.dt

        # Simple invariants
        total_energy = self._compute_energy(pos, vel, params)
        invariants = {"total_energy": float(total_energy), "momentum": float(np.sum(vel, axis=0)[0])}

        new_state = SimulationState(
            positions=pos.tolist(),
            velocities=vel.tolist(),
            metadata={
                **state.metadata,
                "step": state.metadata.get("step", 0) + 1,
                "invariants": invariants
            }
        )
        return new_state

    def _compute_energy(self, pos: np.ndarray, vel: np.ndarray, params: PhysicsParams) -> float:
        """Kinetic + potential. For conservation checks in tests."""
        # Kinetic
        ke = 0.5 * params.mass * np.sum(vel**2)
        # Potential (simplified pair-wise)
        pe = 0.0
        n = len(pos)
        for i in range(n):
            for j in range(i+1, n):
                dist = np.linalg.norm(pos[j] - pos[i])
                if dist > 1e-6:
                    pe -= params.G * params.mass**2 / dist
        return ke + pe
