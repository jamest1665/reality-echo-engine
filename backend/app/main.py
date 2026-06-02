from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .engines.physics import PhysicsEngine, PhysicsParams
from .engines.base import SimulationState
from typing import Dict
import json

app = FastAPI(
    title="Reality Echo Engine",
    version="0.1.0",
    description="Collaborative simulator for physics, biology, and mind cascades."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory sessions for collab (production: replace with Redis + CRDTs)
sessions: Dict[str, Dict] = {}

physics_engine = PhysicsEngine()

@app.get("/")
async def root():
    return {"status": "Reality Echo Engine ready", "engines": ["physics"], "version": "0.1.0"}

@app.post("/api/physics/init")
async def init_physics(params: PhysicsParams):
    """Initialize a new physics universe with dials."""
    state = physics_engine.initialize(params)
    return state.model_dump()

@app.post("/api/physics/step")
async def step_physics(state: SimulationState, params: PhysicsParams):
    """Single step for non-collab or testing."""
    new_state = physics_engine.step(state, params)
    return new_state.model_dump()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Real-time collab: broadcast dial changes and simulation steps."""
    await websocket.accept()
    if session_id not in sessions:
        # Default session state
        default_params = PhysicsParams()
        sessions[session_id] = {
            "params": default_params,
            "state": physics_engine.initialize(default_params),
            "clients": []
        }
    sessions[session_id]["clients"].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "update_dials":
                # Update params (dials)
                sessions[session_id]["params"] = PhysicsParams(**data.get("params", {}))
                # Broadcast to all
                await broadcast(session_id, {"type": "dials_updated", "params": sessions[session_id]["params"].model_dump()})

            elif action == "step":
                current_state = sessions[session_id]["state"]
                new_state = physics_engine.step(current_state, sessions[session_id]["params"])
                sessions[session_id]["state"] = new_state
                await broadcast(session_id, {"type": "update", "state": new_state.model_dump()})

            elif action == "get_invariants":
                invariants = physics_engine.compute_invariants(sessions[session_id]["state"])
                await websocket.send_json({"type": "invariants", "data": invariants})

    except WebSocketDisconnect:
        sessions[session_id]["clients"].remove(websocket)
        if not sessions[session_id]["clients"]:
            del sessions[session_id]  # Cleanup empty session


async def broadcast(session_id: str, message: dict):
    """Helper to broadcast to all clients in session."""
    if session_id in sessions:
        for client in sessions[session_id]["clients"][:]:  # copy to avoid mod during iter
            try:
                await client.send_json(message)
            except:
                # Client dead, remove
                sessions[session_id]["clients"].remove(client)
