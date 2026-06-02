import numpy as np
from typing import Dict, Any
from .base import BaseEngine, SimulationParams, SimulationState
from pydantic import Field

class BiologyParams(SimulationParams):
    """Universe dials for reaction-diffusion biology (Gray-Scott model).
    Classic emergent patterns: spots, stripes, waves from simple rules.
    """
    grid_size: int = Field(128, gt=64, le=256, description="Grid resolution - trade-off perf vs detail")
    Du: float = Field(0.2097, description="Diffusion coefficient U")
    Dv: float = Field(0.105, description="Diffusion coefficient V")
    F: float = Field(0.055, description="Feed rate - major dial for pattern type")
    K: float = Field(0.062, description="Kill rate - tune with F for different regimes")

class BiologyEngine(BaseEngine):
    """Reaction-diffusion engine for biology layer emergence.
    
    Principle: Simple local rules → global patterns (spots, mitosis-like).
    Assumption: Explicit Euler + 4-pt Laplacian (stable for small dt).
    Edge case: High grid_size → memory/CPU; future: GPU or downsample for viz.
    Trade-off: Numerical stability vs. speed (multiple substeps per update).
    """
    def __init__(self):
        super().__init__()
        self.name = "biology"

    def initialize(self, params: BiologyParams) -> SimulationState:
        """Initialize with classic central seed + noise for reproducibility."""
        np.random.seed(42)
        size = params.grid_size
        u = np.ones((size, size))
        v = np.zeros((size, size))
        # Central perturbation for interesting patterns
        r = size // 8
        mid = size // 2
        u[mid-r:mid+r, mid-r:mid+r] = 0.5
        v[mid-r:mid+r, mid-r:mid+r] = 0.25
        # Add noise
        u += 0.01 * np.random.random((size, size))
        v += 0.01 * np.random.random((size, size))
        return SimulationState(
            positions=[],  # Grid-based, not particle
            velocities=[],
            metadata={
                "params": params.model_dump(),
                "step": 0,
                "u": u.tolist(),
                "v": v.tolist(),
                "grid_size": size
            }
        )

    def step(self, state: SimulationState, params: BiologyParams) -> SimulationState:
        """Advance RD simulation. Multiple sub-steps for stability."""
        u = np.array(state.metadata["u"])
        v = np.array(state.metadata["v"])
        size = params.grid_size

        # 4-point Laplacian using roll for periodic boundaries (nice for emergence)
        def laplacian(grid: np.ndarray) -> np.ndarray:
            return (
                np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) +
                np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1) - 4 * grid
            )

        for _ in range(params.steps_per_update):
            lu = laplacian(u)
            lv = laplacian(v)
            uv2 = u * v * v
            du = params.Du * lu - uv2 + params.F * (1 - u)
            dv = params.Dv * lv + uv2 - (params.F + params.K) * v
            u = np.clip(u + du * params.dt, 0.0, 1.0)
            v = np.clip(v + dv * params.dt, 0.0, 1.0)

        invariants = {
            "total_u": float(np.sum(u)),
            "total_v": float(np.sum(v)),
            "pattern_complexity": float(np.std(v))  # proxy for spots/waves
        }

        new_metadata = {
            **state.metadata,
            "step": state.metadata.get("step", 0) + 1,
            "u": u.tolist(),
            "v": v.tolist(),
            "invariants": invariants
        }

        return SimulationState(
            positions=[],
            velocities=[],
            metadata=new_metadata
        )

    def compute_invariants(self, state: SimulationState) -> Dict[str, float]:
        """Return biology invariants from metadata."""
        return state.metadata.get("invariants", {"total_u": 0.0, "total_v": 0.0})
