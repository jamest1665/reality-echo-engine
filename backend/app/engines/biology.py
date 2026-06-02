import numpy as np
from typing import Dict, Any
from .base import BaseEngine, SimulationParams, SimulationState
from pydantic import Field

class BiologyParams(SimulationParams):
    """Universe dials for Gray-Scott reaction-diffusion biology engine.
    Classic parameters for emergent patterns (spots, stripes, waves).
    """
    grid_size: int = Field(128, gt=32, le=512, description="Resolution of chemical grid")
    F: float = Field(0.055, ge=0.0, le=0.1, description="Feed rate - controls pattern type")
    K: float = Field(0.062, ge=0.0, le=0.1, description="Kill rate - tunes morphology")
    Du: float = 0.16  # Diffusion rate for U (prey)
    Dv: float = 0.08  # Diffusion rate for V (predator)
    dt: float = 1.0   # Larger timestep for RD stability

    model_config = {"extra": "forbid"}

class BiologyEngine(BaseEngine):
    """Gray-Scott reaction-diffusion engine for emergent biology patterns.
    
    From first principles: Local reaction rules + diffusion → global cascades (spots, mazes, etc.).
    Supports hypothesis testing on parameter space for 'life-like' invariants.
    Trade-offs: Explicit Euler on grid (fast but can be unstable at extremes → clipped).
    Edge cases: High F/K → blowup (guarded); large grid → perf (NumPy vectorized).
    Assumption: 2D toroidal grid; state uses metadata for grid data (positions empty).
    """
    def __init__(self):
        super().__init__()
        self.name = "biology"

    def initialize(self, params: BiologyParams) -> SimulationState:
        """Initialize chemicals U (prey) and V (predator) with seed perturbation."""
        np.random.seed(42)  # Reproducibility
        size = params.grid_size
        u = np.ones((size, size))  # U everywhere
        v = np.zeros((size, size)) # V zero

        # Seed perturbation in center
        mid = size // 2
        r = size // 10
        u[mid-r:mid+r, mid-r:mid+r] = 0.5 + 0.1 * np.random.rand(2*r, 2*r)
        v[mid-r:mid+r, mid-r:mid+r] = 0.25 + 0.1 * np.random.rand(2*r, 2*r)

        # Store grid in metadata to fit SimulationState interface
        return SimulationState(
            positions=[],  # Not used for grid-based
            velocities=[], # Not used
            metadata={
                "params": params.model_dump(),
                "step": 0,
                "grid_u": u.tolist(),
                "grid_v": v.tolist(),
                "engine_type": "biology"
            }
        )

    def step(self, state: SimulationState, params: BiologyParams) -> SimulationState:
        """One Gray-Scott step: diffusion + reaction + update."""
        # Extract grids
        u = np.array(state.metadata["grid_u"])
        v = np.array(state.metadata["grid_v"])
        size = params.grid_size

        # Laplacian (periodic boundaries via np.roll)
        def laplacian(grid):
            return (
                np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) +
                np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1) -
                4 * grid
            )

        lap_u = laplacian(u)
        lap_v = laplacian(v)

        # Reaction terms - standard Gray-Scott
        du = params.Du * lap_u - u * v * v + params.F * (1 - u)
        dv = params.Dv * lap_v + u * v * v - (params.F + params.K) * v

        # Update
        u += du * params.dt
        v += dv * params.dt

        # Guards against NaN/extremes
        u = np.clip(u, 0.0, 1.0)
        v = np.clip(v, 0.0, 1.0)

        # Invariants: e.g., total 'mass' or pattern metrics
        total_u = float(np.sum(u))
        total_v = float(np.sum(v))
        invariants = {
            "total_u": total_u,
            "total_v": total_v,
            "pattern_complexity": float(np.std(u))  # proxy for emergence
        }

        new_metadata = {
            **state.metadata,
            "step": state.metadata.get("step", 0) + params.steps_per_update,
            "grid_u": u.tolist(),
            "grid_v": v.tolist(),
            "invariants": invariants
        }

        return SimulationState(
            positions=[],
            velocities=[],
            metadata=new_metadata
        )

    def compute_invariants(self, state: SimulationState) -> Dict[str, float]:
        """Biology-specific invariants."""
        if "invariants" in state.metadata:
            return state.metadata["invariants"]
        return {"total_u": 0.0, "total_v": 0.0}
"