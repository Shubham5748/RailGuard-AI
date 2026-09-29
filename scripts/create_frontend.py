import os

files = {
    "frontend/src/index.css": """
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #0f172a;
  color: #f8fafc;
}
""",
    "frontend/tailwind.config.js": """
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
""",
    "frontend/src/main.jsx": """
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
    "frontend/src/App.jsx": """
import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle, Train, Users, ShieldAlert, Activity, ShieldCheck, AlertOctagon } from 'lucide-react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/ws/monitor';

function App() {
  const [status, setStatus] = useState({ is_monitoring: false });
  const [telemetry, setTelemetry] = useState({
    train_state: 'STOPPED',
    safe_count: 0,
    danger_count: 0,
    passengers: {},
    alerts: []
  });
  const [frame, setFrame] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [analytics, setAnalytics] = useState({ total_incidents: 0, critical_alerts: 0, high_alerts: 0 });
  const wsRef = useRef(null);

  useEffect(() => {
    fetchStatus();
    fetchIncidents();
    fetchAnalytics();
    
    // Poll analytics & incidents
    const interval = setInterval(() => {
      fetchIncidents();
      fetchAnalytics();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (status.is_monitoring) {
      connectWebSocket();
    } else {
      if (wsRef.current) {
        wsRef.current.close();
      }
    }
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, [status.is_monitoring]);

  const connectWebSocket = () => {
    wsRef.current = new WebSocket(WS_URL);
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setTelemetry(data.telemetry);
      setFrame(data.frame);
    };
    wsRef.current.onerror = (error) => {
      console.error("WebSocket error", error);
    };
  };

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API_URL}/status`);
      setStatus(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const fetchIncidents = async () => {
    try {
      const res = await axios.get(`${API_URL}/incidents`);
      setIncidents(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await axios.get(`${API_URL}/analytics`);
      setAnalytics(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const toggleMonitoring = async () => {
    try {
      if (status.is_monitoring) {
        await axios.post(`${API_URL}/monitor/stop`);
      } else {
        await axios.post(`${API_URL}/monitor/start`);
      }
      fetchStatus();
    } catch (error) {
      alert("Error starting/stopping monitor. Ensure a video is uploaded if no demo exists.");
    }
  };

  const uploadVideo = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      await axios.post(`${API_URL}/video/upload`, formData);
      alert('Video uploaded successfully!');
    } catch (error) {
      console.error(error);
      alert('Video upload failed');
    }
  };

  // Compute current risk based on telemetry alerts
  let currentRisk = "LOW";
  let riskColor = "text-green-500";
  if (telemetry.alerts.length > 0) {
    const hasCritical = telemetry.alerts.some(a => a.risk_level === 'CRITICAL');
    if (hasCritical) {
      currentRisk = "CRITICAL";
      riskColor = "text-red-500";
    } else {
      currentRisk = "HIGH";
      riskColor = "text-orange-500";
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6 flex flex-col font-sans text-slate-100">
      <header className="flex justify-between items-center mb-8 border-b border-slate-700 pb-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <ShieldAlert className="text-blue-500" />
            RAILGUARD AI
          </h1>
          <p className="text-slate-400 text-sm">Intelligent Railway Platform Safety Monitoring System</p>
        </div>
        <div className="flex gap-4">
          <div className={`px-4 py-2 rounded-full border ${status.is_monitoring ? 'border-green-500 text-green-500 bg-green-500/10' : 'border-slate-500 text-slate-500'}`}>
            {status.is_monitoring ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
          </div>
          <button onClick={toggleMonitoring} className={`px-4 py-2 rounded font-semibold ${status.is_monitoring ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'}`}>
            {status.is_monitoring ? 'Stop Monitoring' : 'Start Monitoring'}
          </button>
          <div>
            <label className="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded cursor-pointer font-semibold block text-center">
              Upload Video
              <input type="file" className="hidden" accept="video/mp4" onChange={uploadVideo} />
            </label>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        {/* Main Video Area */}
        <div className="col-span-1 lg:col-span-3 bg-slate-800 rounded-lg shadow-xl overflow-hidden border border-slate-700 flex flex-col">
          <div className="p-3 bg-slate-800/80 border-b border-slate-700 flex justify-between items-center">
            <span className="font-semibold flex items-center gap-2"><Activity size={18} /> LIVE PLATFORM CAMERA</span>
            <span className="text-xs text-slate-400 uppercase tracking-wider">{status.is_monitoring ? 'Processed Video Feed' : 'Offline'}</span>
          </div>
          <div className="bg-black flex-1 min-h-[500px] flex items-center justify-center relative">
            {status.is_monitoring && frame ? (
              <img src={`data:image/jpeg;base64,${frame}`} alt="Live Feed" className="w-full h-full object-contain" />
            ) : (
              <div className="text-slate-600 flex flex-col items-center">
                <AlertOctagon size={48} className="mb-4 opacity-50" />
                <p>No Active Feed</p>
                <p className="text-sm">Click "Start Monitoring" to begin AI processing.</p>
              </div>
            )}
            
            {/* Overlay Status when active */}
            {status.is_monitoring && (
               <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-sm p-3 rounded-lg border border-slate-700">
                  <div className={`text-xl font-bold ${riskColor} flex items-center gap-2`}>
                    Risk: {currentRisk}
                  </div>
               </div>
            )}
          </div>
        </div>

        {/* Side Stats */}
        <div className="flex flex-col gap-4">
          <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 flex flex-col gap-2">
            <span className="text-slate-400 text-sm font-semibold flex items-center gap-2"><Train size={16} /> TRAIN STATUS</span>
            <span className={`text-2xl font-bold ${telemetry.train_state === 'APPROACHING' ? 'text-orange-500' : 'text-blue-400'}`}>
              {telemetry.train_state}
            </span>
          </div>

          <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 flex flex-col gap-2">
            <span className="text-slate-400 text-sm font-semibold flex items-center gap-2"><ShieldCheck size={16} /> SAFE PASSENGERS</span>
            <span className="text-3xl font-bold text-green-500">{telemetry.safe_count}</span>
          </div>

          <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 flex flex-col gap-2">
            <span className="text-slate-400 text-sm font-semibold flex items-center gap-2"><AlertTriangle size={16} /> DANGER ZONE</span>
            <span className={`text-3xl font-bold ${telemetry.danger_count > 0 ? 'text-red-500' : 'text-slate-300'}`}>{telemetry.danger_count}</span>
          </div>

          <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 flex flex-col gap-2 flex-1 overflow-auto">
             <span className="text-slate-400 text-sm font-semibold flex items-center gap-2"><Activity size={16} /> ACTIVE ALERTS</span>
             <div className="flex flex-col gap-3 mt-2">
                {telemetry.alerts.length === 0 ? (
                  <div className="text-slate-500 text-sm italic">No active alerts.</div>
                ) : (
                  telemetry.alerts.map((a, i) => (
                    <div key={i} className="bg-red-900/40 border border-red-500/50 p-3 rounded text-sm">
                      <div className="font-bold text-red-400 mb-1">⚠ SAFETY ALERT</div>
                      <div>Passenger #{a.passenger_id} in danger zone</div>
                      <div>Duration: {a.danger_duration.toFixed(1)}s</div>
                      <div>Risk: {a.risk_level}</div>
                    </div>
                  ))
                )}
             </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Incidents & Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-lg p-5 border border-slate-700">
          <h2 className="text-xl font-bold mb-4 border-b border-slate-700 pb-2">Incident History</h2>
          <div className="overflow-x-auto max-h-[300px] overflow-y-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-400 uppercase bg-slate-900/50">
                <tr>
                  <th className="px-4 py-3 rounded-tl">Time</th>
                  <th className="px-4 py-3">Pass ID</th>
                  <th className="px-4 py-3">Train</th>
                  <th className="px-4 py-3">Dur (s)</th>
                  <th className="px-4 py-3">Risk</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map(inc => (
                  <tr key={inc.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                    <td className="px-4 py-3">{new Date(inc.timestamp).toLocaleTimeString()}</td>
                    <td className="px-4 py-3">#{inc.passenger_id}</td>
                    <td className="px-4 py-3">{inc.train_state}</td>
                    <td className="px-4 py-3">{inc.danger_duration.toFixed(1)}</td>
                    <td className="px-4 py-3 text-red-400 font-semibold">{inc.risk_level}</td>
                  </tr>
                ))}
                {incidents.length === 0 && (
                  <tr>
                    <td colSpan="5" className="px-4 py-8 text-center text-slate-500 italic">No incidents recorded yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-5 border border-slate-700">
          <h2 className="text-xl font-bold mb-4 border-b border-slate-700 pb-2">System Analytics</h2>
          <div className="grid grid-cols-2 gap-4">
             <div className="bg-slate-900 p-4 rounded text-center border border-slate-700">
               <div className="text-slate-400 text-sm mb-1">Total Incidents</div>
               <div className="text-3xl font-bold">{analytics.total_incidents}</div>
             </div>
             <div className="bg-slate-900 p-4 rounded text-center border border-slate-700">
               <div className="text-slate-400 text-sm mb-1">Critical Alerts</div>
               <div className="text-3xl font-bold text-red-500">{analytics.critical_alerts}</div>
             </div>
             <div className="bg-slate-900 p-4 rounded text-center border border-slate-700">
               <div className="text-slate-400 text-sm mb-1">High Alerts</div>
               <div className="text-3xl font-bold text-orange-500">{analytics.high_alerts}</div>
             </div>
             <div className="bg-slate-900 p-4 rounded flex items-center justify-center border border-slate-700">
               <div className="text-slate-500 text-sm italic">Analytics synced from PostgreSQL DB</div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
"""
}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content.strip())

print("Frontend files created successfully!")
