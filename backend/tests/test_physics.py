import pytest
import numpy as np
from app.engines.physics import PhysicsEngine, PhysicsParams
from app.engines.base import SimulationState

def test_energy_conservation():
    """Invariant test: energy should be roughly conserved (numerical drift expected)."""
    engine = PhysicsEngine()
    params = PhysicsParams(num_particles=10, dt=0.001, G=1.0)
    state = engine.initialize(params)
    
    initial_energy = engine._compute_energy(np.array(state.positions), np.array(state.velocities), params)
    
    for _ in range(50):
        state = engine.step(state, params)
    
    final_energy = engine._compute_energy(np.array(state.positions), np.array(state.velocities), params)
    
    # Allow small drift due to Euler method (trade-off vs accuracy)
    assert abs(final_energy - initial_energy) / abs(initial_energy) < 0.15, "Energy not approximately conserved"
