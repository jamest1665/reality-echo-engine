import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface ParticleState {
  positions: number[][];
  velocities: number[][];
  metadata: any;
}

const App: React.FC = () => {
  const [sessionId] = useState('demo-session-1'); // Simple fixed for prototype
  const [params, setParams] = useState({ G: 1.0, num_particles: 30, dt: 0.01 });
  const [state, setState] = useState<ParticleState | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WS
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => console.log('Connected to Reality Echo session');
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'update') {
        setState(msg.state);
      } else if (msg.type === 'dials_updated') {
        setParams(msg.params);
      }
    };

    // Init simulation
    fetch('http://localhost:8000/api/physics/init', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(r => r.json()).then(initialState => setState(initialState));

    return () => ws.close();
  }, []);

  useEffect(() => {
    if (!state || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Simple viz: draw particles
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#22c55e';
    state.positions.forEach(([x, y]) => {
      const scaledX = (x + 10) * 20; // rough scale
      const scaledY = (y + 10) * 20;
      ctx.fillRect(scaledX, scaledY, 4, 4);
    });
  }, [state]);

  const handleStep = () => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ action: 'step' }));
    }
  };

  const updateDial = (key: string, value: number) => {
    const newParams = { ...params, [key]: value };
    setParams(newParams);
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ action: 'update_dials', params: newParams }));
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Reality Echo Engine</h1>
      
      <div className="grid grid-cols-2 gap-8">
        {/* Controls / Dials */}
        <div>
          <h2 className="text-2xl mb-4">Universe Dials</h2>
          <div className="space-y-4">
            <label>G: <input type="range" min="0.1" max="10" step="0.1" value={params.G} onChange={e => updateDial('G', parseFloat(e.target.value))} /></label>
            <label>Particles: <input type="number" value={params.num_particles} onChange={e => updateDial('num_particles', parseInt(e.target.value))} /></label>
            <label>dt: <input type="range" min="0.001" max="0.1" step="0.001" value={params.dt} onChange={e => updateDial('dt', parseFloat(e.target.value))} /></label>
          </div>
          <button onClick={handleStep} className="mt-6 px-6 py-3 bg-green-600 text-white rounded">Step Simulation</button>
        </div>

        {/* Visualization */}
        <div>
          <canvas ref={canvasRef} width={600} height={600} className="border border-gray-300 bg-black" />
          {state && <p className="mt-2 text-sm">Step: {state.metadata?.step || 0} | Invariants: {JSON.stringify(state.metadata?.invariants || {})}</p>}
        </div>
      </div>

      <footer className="mt-12 text-xs opacity-60">
        Collaborative physics prototype • Extend to biology/mind cascades • James Ryan
      </footer>
    </div>
  );
};

export default App;
