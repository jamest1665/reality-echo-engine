from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .engines.physics import PhysicsEngine, PhysicsParams
from .engines.biology import BiologyEngine, BiologyParams
from .engines.base import SimulationState
from typing import Dict

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

# Engine registry for modularity and future extensions (mind next)
physics_engine = PhysicsEngine()
biology_engine = BiologyEngine()
engine_map = {
    "physics": physics_engine,
    "biology": biology_engine,
}
param_map = {
    "physics": PhysicsParams,
    "biology": BiologyParams,
}

@app.get("/")
async def root():
    return {"status": "Reality Echo Engine ready", "engines": ["physics", "biology"], "version": "0.1.0"}

# Physics endpoints (backward compatible)
@app.post("/api/physics/init")
async def init_physics(params: PhysicsParams):
    state = physics_engine.initialize(params)
    return state.model_dump()

@app.post("/api/physics/step")
async def step_physics(state: SimulationState, params: PhysicsParams):
    new_state = physics_engine.step(state, params)
    return new_state.model_dump()

# Biology endpoints
@app.post("/api/biology/init")
async def init_biology(params: BiologyParams):
    """Initialize biology universe with RD dials."""
    state = biology_engine.initialize(params)
    return state.model_dump()

@app.post("/api/biology/step")
async def step_biology(state: SimulationState, params: BiologyParams):
    """Step biology simulation."""
    new_state = biology_engine.step(state, params)
    return new_state.model_dump()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Real-time collab: now supports engine switching for physics/biology."""
    await websocket.accept()
    if session_id not in sessions:
        # Default to physics for backward compat
        default_params = PhysicsParams()
        sessions[session_id] = {
            "engine_type": "physics",
            "params": default_params,
            "state": physics_engine.initialize(default_params),
            "clients": []
        }
    sessions[session_id]["clients"].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            engine_type = data.get("engine_type", sessions[session_id].get("engine_type", "physics"))

            if engine_type not in engine_map:
                await websocket.send_json({"type": "error", "message": "Unknown engine"})
                continue

            current_engine = engine_map[engine_type]
            params_class = param_map[engine_type]

            if action == "update_dials":
                new_params = params_class(**data.get("params", {}))
                sessions[session_id]["params"] = new_params
                sessions[session_id]["engine_type"] = engine_type
                await broadcast(session_id, {"type": "dials_updated", "engine_type": engine_type, "params": new_params.model_dump()})

            elif action == "step":
                current_state = sessions[session_id]["state"]
                new_state = current_engine.step(current_state, sessions[session_id]["params"])
                sessions[session_id]["state"] = new_state
                await broadcast(session_id, {"type": "update", "engine_type": engine_type, "state": new_state.model_dump()})

            elif action == "set_engine":
                # Switch engine and reinitialize
                sessions[session_id]["engine_type"] = engine_type
                default_params = params_class()
                sessions[session_id]["params"] = default_params
                sessions[session_id]["state"] = current_engine.initialize(default_params)
                await broadcast(session_id, {"type": "engine_switched", "engine_type": engine_type, "state": sessions[session_id]["state"].model_dump()})

            elif action == "get_invariants":
                invariants = current_engine.compute_invariants(sessions[session_id]["state"])
                await websocket.send_json({"type": "invariants", "engine_type": engine_type, "data": invariants})

    except WebSocketDisconnect:
        sessions[session_id]["clients"].remove(websocket)
        if not sessions[session_id]["clients"]:
            del sessions[session_id]


async def broadcast(session_id: str, message: dict):
    """Helper to broadcast to all clients in session."""
    if session_id in sessions:
        for client in sessions[session_id]["clients"][:]:  # copy to avoid mod during iter
            try:
                await client.send_json(message)
            except:
                sessions[session_id]["clients"].remove(client)
