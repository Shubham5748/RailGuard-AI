import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle, Train, Users, ShieldAlert, Activity, ShieldCheck, AlertOctagon, RefreshCw } from 'lucide-react';
import axios from 'axios';

// Dynamic API & WebSocket URLs based on current browser window location
const API_URL = typeof window !== 'undefined' ? window.location.origin + '/api' : '/api';
const WS_PROTOCOL = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const WS_URL = typeof window !== 'undefined' ? WS_PROTOCOL + window.location.host + '/ws/monitor' : '';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-6 text-center">
          <ShieldAlert size={64} className="text-red-500 mb-4" />
          <h1 className="text-2xl font-bold mb-2">Something went wrong rendering the UI</h1>
          <p className="text-slate-400 max-w-md mb-6">{this.state.error?.message || "An unexpected error occurred."}</p>
          <button onClick={() => window.location.reload()} className="px-6 py-2 bg-blue-600 rounded font-semibold hover:bg-blue-700">
            Reload Dashboard
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function Dashboard() {
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
  const [connectionMode, setConnectionMode] = useState('connecting');
  const wsRef = useRef(null);

  useEffect(() => {
    fetchStatus();
    fetchIncidents();
    fetchAnalytics();
    
    // Poll analytics & incidents periodically
    const interval = setInterval(() => {
      fetchIncidents();
      fetchAnalytics();
      fetchStatus();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // Frame polling fallback: if WebSocket doesn't connect, poll /api/monitor/frame
  useEffect(() => {
    let framePoll;
    if (status.is_monitoring && connectionMode !== 'websocket') {
      framePoll = setInterval(async () => {
        try {
          const res = await axios.get(`${API_URL}/monitor/frame`);
          if (res.data) {
            if (res.data.telemetry) setTelemetry(res.data.telemetry);
            if (res.data.frame) setFrame(res.data.frame);
          }
        } catch (e) {
          // ignore transient poll errors
        }
      }, 100);
    }
    return () => {
      if (framePoll) clearInterval(framePoll);
    };
  }, [status.is_monitoring, connectionMode]);

  useEffect(() => {
    if (status.is_monitoring) {
      connectWebSocket();
    } else {
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (e) {}
      }
      setConnectionMode('idle');
    }
    return () => {
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (e) {}
      }
    };
  }, [status.is_monitoring]);

  const connectWebSocket = () => {
    try {
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (e) {}
      }
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionMode('websocket');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.telemetry) setTelemetry(data.telemetry);
          if (data.frame) setFrame(data.frame);
        } catch (err) {
          console.error("Frame parse error", err);
        }
      };

      ws.onerror = (error) => {
        console.warn("WebSocket error, falling back to HTTP streaming:", error);
        setConnectionMode('http-fallback');
      };

      ws.onclose = () => {
        if (status.is_monitoring) {
          setConnectionMode('http-fallback');
        }
      };
    } catch (err) {
      console.warn("WebSocket initialization failed, using HTTP stream fallback:", err);
      setConnectionMode('http-fallback');
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API_URL}/status`);
      if (res.data) setStatus(res.data);
    } catch (error) {
      console.error("Status fetch error", error);
    }
  };

  const fetchIncidents = async () => {
    try {
      const res = await axios.get(`${API_URL}/incidents`);
      if (Array.isArray(res.data)) setIncidents(res.data);
    } catch (error) {
      console.error("Incidents fetch error", error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await axios.get(`${API_URL}/analytics`);
      if (res.data) setAnalytics(res.data);
    } catch (error) {
      console.error("Analytics fetch error", error);
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
      alert("Error toggling monitoring. Please try again.");
    }
  };

  const uploadVideo = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      await axios.post(`${API_URL}/video/upload`, formData);
      alert('Video uploaded successfully! Click Start Monitoring to begin processing.');
      fetchStatus();
    } catch (error) {
      console.error("Upload error", error);
      alert('Video upload failed');
    }
  };

  // Safe alerts list
  const alertsList = Array.isArray(telemetry?.alerts) ? telemetry.alerts : [];

  // Compute current risk based on telemetry alerts
  let currentRisk = "LOW";
  let riskColor = "text-green-500";
  if (alertsList.length > 0) {
    const hasCritical = alertsList.some(a => a?.risk_level === 'CRITICAL');
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
      <header className="flex flex-wrap justify-between items-center mb-8 border-b border-slate-700 pb-4 gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <ShieldAlert className="text-blue-500" />
            RAILGUARD AI
          </h1>
          <p className="text-slate-400 text-sm">Intelligent Railway Platform Safety Monitoring System</p>
        </div>
        <div className="flex flex-wrap gap-4 items-center">
          <div className={`px-4 py-2 rounded-full border text-sm font-semibold flex items-center gap-2 ${status.is_monitoring ? 'border-green-500 text-green-500 bg-green-500/10' : 'border-slate-500 text-slate-400'}`}>
            <span className={`w-2 h-2 rounded-full ${status.is_monitoring ? 'bg-green-500 animate-pulse' : 'bg-slate-500'}`}></span>
            {status.is_monitoring ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
          </div>
          <button onClick={toggleMonitoring} className={`px-5 py-2 rounded font-semibold transition ${status.is_monitoring ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'}`}>
            {status.is_monitoring ? 'Stop Monitoring' : 'Start Monitoring'}
          </button>
          <div>
            <label className="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded cursor-pointer font-semibold block text-center transition">
              Upload Video
              <input type="file" className="hidden" accept="video/mp4,video/*" onChange={uploadVideo} />
            </label>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        {/* Main Video Area */}
        <div className="col-span-1 lg:col-span-3 bg-slate-800 rounded-lg shadow-xl overflow-hidden border border-slate-700 flex flex-col">
          <div className="p-3 bg-slate-800/80 border-b border-slate-700 flex justify-between items-center">
            <span className="font-semibold flex items-center gap-2"><Activity size={18} /> LIVE PLATFORM CAMERA</span>
            <span className="text-xs text-slate-400 uppercase tracking-wider">
              {status.is_monitoring ? 'AI Video Feed' : 'Offline'}
            </span>
          </div>
          <div className="bg-black flex-1 min-h-[460px] flex items-center justify-center relative">
            {status.is_monitoring && frame ? (
              <img src={`data:image/jpeg;base64,${frame}`} alt="Live AI Feed" className="w-full h-full object-contain" />
            ) : (
              <div className="text-slate-500 flex flex-col items-center p-8 text-center">
                <AlertOctagon size={48} className="mb-4 opacity-40 text-blue-400" />
                <p className="text-lg font-medium text-slate-300">No Active Feed</p>
                <p className="text-sm text-slate-400 mt-1">Click "Start Monitoring" or upload a CCTV video to begin AI detection.</p>
              </div>
            )}
            
            {/* Live Risk Badge overlay */}
            {status.is_monitoring && (
               <div className="absolute top-4 right-4 bg-black/70 backdrop-blur-sm px-4 py-2 rounded-lg border border-slate-700 shadow">
                  <div className={`text-lg font-bold ${riskColor} flex items-center gap-2`}>
                    Risk: {currentRisk}
                  </div>
               </div>
            )}
          </div>
        </div>

        {/* Side Stats */}
        <div className="flex flex-col gap-4">
          <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 flex flex-col gap-1">
            <span className="text-slate-400 text-sm font-semibold flex items-center gap-2"><Train size={16} /> TRAIN STATUS</span>
            <span className={`text-2xl font-bold ${telemetry?.train_state === 'APPROACHING' ? 'text-orange-500' : 'text-blue-400'}`}>
              {telemetry?.train_state || 'STOPPED'}
            </span>
          </div>

          <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 flex flex-col gap-1">
            <span className="text-slate-400 text-sm font-semibold flex items-center gap-2"><ShieldCheck size={16} /> SAFE PASSENGERS</span>
            <span className="text-3xl font-bold text-green-500">{telemetry?.safe_count ?? 0}</span>
          </div>

          <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 flex flex-col gap-1">
            <span className="text-slate-400 text-sm font-semibold flex items-center gap-2"><AlertTriangle size={16} /> DANGER ZONE</span>
            <span className={`text-3xl font-bold ${(telemetry?.danger_count ?? 0) > 0 ? 'text-red-500' : 'text-slate-300'}`}>
              {telemetry?.danger_count ?? 0}
            </span>
          </div>

          <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 flex flex-col gap-2 flex-1 overflow-auto max-h-[220px]">
             <span className="text-slate-400 text-sm font-semibold flex items-center gap-2"><Activity size={16} /> ACTIVE ALERTS</span>
             <div className="flex flex-col gap-2 mt-1">
                {alertsList.length === 0 ? (
                  <div className="text-slate-500 text-sm italic">No active danger alerts.</div>
                ) : (
                  alertsList.map((a, i) => (
                    <div key={i} className="bg-red-900/40 border border-red-500/50 p-2.5 rounded text-sm">
                      <div className="font-bold text-red-400 mb-0.5">⚠ SAFETY ALERT</div>
                      <div>Passenger #{a?.passenger_id ?? i} in danger zone</div>
                      <div>Duration: {Number(a?.danger_duration ?? 0).toFixed(1)}s</div>
                      <div className="font-semibold text-red-300">Risk: {a?.risk_level ?? 'CRITICAL'}</div>
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
          <div className="overflow-x-auto max-h-[280px] overflow-y-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-400 uppercase bg-slate-900/50 sticky top-0">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Pass ID</th>
                  <th className="px-4 py-3">Train</th>
                  <th className="px-4 py-3">Dur (s)</th>
                  <th className="px-4 py-3">Risk</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map(inc => (
                  <tr key={inc.id || Math.random()} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                    <td className="px-4 py-3">{inc.timestamp ? new Date(inc.timestamp).toLocaleTimeString() : 'Recent'}</td>
                    <td className="px-4 py-3">#{inc.passenger_id}</td>
                    <td className="px-4 py-3">{inc.train_state}</td>
                    <td className="px-4 py-3">{Number(inc.danger_duration || 0).toFixed(1)}</td>
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
               <div className="text-3xl font-bold">{analytics.total_incidents ?? 0}</div>
             </div>
             <div className="bg-slate-900 p-4 rounded text-center border border-slate-700">
               <div className="text-slate-400 text-sm mb-1">Critical Alerts</div>
               <div className="text-3xl font-bold text-red-500">{analytics.critical_alerts ?? 0}</div>
             </div>
             <div className="bg-slate-900 p-4 rounded text-center border border-slate-700">
               <div className="text-slate-400 text-sm mb-1">High Alerts</div>
               <div className="text-3xl font-bold text-orange-500">{analytics.high_alerts ?? 0}</div>
             </div>
             <div className="bg-slate-900 p-4 rounded flex items-center justify-center border border-slate-700">
               <div className="text-slate-400 text-xs text-center">Real-time Safety Monitoring Engine Active</div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  );
}
