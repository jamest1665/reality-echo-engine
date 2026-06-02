# Reality Echo Engine

Collaborative universe simulator. Tune constants, symmetries, and emergence rules. Observe physics → biology → mind cascades. Spot invariants and test hypotheses in real time with collaborators.

## Quick Start

1. Clone the repo
2. `docker compose up --build`
3. Open http://localhost:3000

## Features

- Modular engines (Physics prototype ready; Biology & Mind extensible)
- Real-time collaborative sessions via WebSockets
- Interactive dials for universe parameters
- Visualization of particle cascades and invariants
- Hypothesis testing tools

## Architecture

- **Backend**: FastAPI + NumPy for simulation engines
- **Frontend**: React + Vite + Canvas/Three.js
- **Collab**: Shared sessions with broadcast updates

See `docs/architecture.md` for details.

## Extending Engines

See `backend/app/engines/base.py` — subclass and implement `step()` and `compute_invariants()`.

**Made by James Ryan with principal engineering standards.**
