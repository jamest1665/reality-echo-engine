from pydantic import BaseModel
from typing import Dict, Any
import numpy as np
from abc import ABC, abstractmethod

class SimulationParams(BaseModel):
    """Base parameters for any engine dial set."""
    dt: float = 0.01
    steps_per_update: int = 10

class SimulationState(BaseModel):
    """Core state shared across engines."""
    positions: list[list[float]]  # or np.array serialized
    velocities: list[list[float]]
    metadata: Dict[str, Any] = {}

class BaseEngine(ABC):
    """Abstract base for all universe simulation engines.
    
    Principle: Every engine must implement step() and invariants() for reproducibility.
    """
    def __init__(self):
        self.name = "base"

    @abstractmethod
    def initialize(self, params: SimulationParams) -> SimulationState:
        pass

    @abstractmethod
    def step(self, state: SimulationState, params: SimulationParams) -> SimulationState:
        """Advance simulation one tick. Flag assumptions: Euler integration for speed."""
        pass

    def compute_invariants(self, state: SimulationState) -> Dict[str, float]:
        """Spot conserved quantities. Subclasses override for energy, momentum, etc."""
        return {"placeholder_invariant": 1.0}
