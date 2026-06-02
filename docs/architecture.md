# Architecture

## First Principles
- Modularity: Engines inherit from BaseEngine for easy extension (physics → biology via reaction-diffusion, mind via simple agents).
- Reproducibility: Fixed seeds, deterministic steps.
- Collab: WS sessions with optimistic updates + server authority.

## Trade-offs & Edge Cases
- In-memory sessions: Fast for prototype; scale with Redis later.
- Euler integration: Fast but drifts; future symplectic or RK4.
- Viz: 2D Canvas; 3D with Three.js in v0.2.
- Numerical stability: Softening + bounds checks.

## How to add new engine
1. Subclass BaseEngine
2. Implement initialize/step/compute_invariants
3. Register in main.py routers

James' note: Prioritize invariants detection as the 'echo' of reality.
